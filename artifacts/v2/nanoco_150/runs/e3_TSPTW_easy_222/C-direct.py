import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = params["num_nodes"]
    dist = params["distance_matrix"]
    time_windows = params["time_windows"]
    service_times = params["service_times"]
    horizon = params["horizon"]

    nodes = list(range(num_nodes))
    stations = list(range(1, num_nodes))  # nodes 1..7

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = 1 if truck travels directly from i to j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # t[i] = arrival time at node i (for stations: within their time window)
    # For node 0 we use t[0] as the *departure* time from the hub.
    t = {}
    for i in nodes:
        t[i] = model.addVar(
            lb=time_windows[i][0],
            ub=time_windows[i][1],
            vtype=GRB.CONTINUOUS,
            name=f"t_{i}"
        )

    # t_ret = actual return arrival time at hub (separate from departure t[0])
    t_ret = model.addVar(lb=0.0, ub=float(horizon), vtype=GRB.CONTINUOUS, name="t_ret")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each station entered exactly once
    for j in stations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each station exited exactly once
    for i in stations:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if i != j) == 1,
            name=f"exit_{i}"
        )

    # Hub departs exactly once
    model.addConstr(
        gp.quicksum(x[0, j] for j in stations) == 1,
        name="hub_depart"
    )

    # Hub returns exactly once
    model.addConstr(
        gp.quicksum(x[i, 0] for i in stations) == 1,
        name="hub_return"
    )

    # Big-M value
    big_M = float(horizon) + max(dist[i][j] for i in nodes for j in nodes if i != j)

    # Time progression from hub (node 0) to stations
    for j in stations:
        model.addConstr(
            t[j] >= t[0] + service_times[0] + dist[0][j] - big_M * (1 - x[0, j]),
            name=f"time_0_{j}"
        )

    # Time progression between stations
    for i in stations:
        for j in stations:
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + service_times[i] + dist[i][j] - big_M * (1 - x[i, j]),
                    name=f"time_{i}_{j}"
                )

    # Time progression from stations back to hub (use t_ret)
    for i in stations:
        model.addConstr(
            t_ret >= t[i] + service_times[i] + dist[i][0] - big_M * (1 - x[i, 0]),
            name=f"time_{i}_ret"
        )

    # Return must be within horizon
    model.addConstr(t_ret <= horizon, name="ret_horizon")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.TIME_LIMIT and model.SolCount > 0:
        return {"objective": float(model.ObjVal), "status": "time_limit_feasible"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}