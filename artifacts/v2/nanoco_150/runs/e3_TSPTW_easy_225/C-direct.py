import gurobipy as gp
from gurobipy import GRB

def solve(params):
    travel_time = params["travel_time"]
    time_window_start = params["time_window_start"]
    time_window_end = params["time_window_end"]
    planning_horizon = params["planning_horizon"]
    service_time = params["service_time"]

    n = 9
    nodes = list(range(n))
    depot = 0
    clients = list(range(1, n))

    # Build cost matrix
    c = {(i, j): travel_time[i][j] for i in nodes for j in nodes}

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[i,j] = 1 if courier travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # t[i] = arrival time at node i
    t = model.addVars(nodes, lb=0.0, ub=planning_horizon, vtype=GRB.CONTINUOUS, name="t")

    # Objective: minimize total travel time
    model.setObjective(
        gp.quicksum(c[i, j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each client node is entered exactly once
    for j in clients:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes) == 1, name=f"enter_{j}")

    # Each client node is exited exactly once
    for i in clients:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes) == 1, name=f"exit_{i}")

    # Depot: depart exactly once
    model.addConstr(gp.quicksum(x[depot, j] for j in clients) == 1, name="depot_out")

    # Depot: return exactly once
    model.addConstr(gp.quicksum(x[i, depot] for i in clients) == 1, name="depot_in")

    # Time window constraints at depot
    model.addConstr(t[depot] == 0, name="depot_start")

    # Time propagation and time windows (MTZ-style with big-M)
    big_M = planning_horizon
    for i in nodes:
        for j in clients:
            if i != j:
                # If x[i,j]=1 then t[j] >= t[i] + service_time[i] + travel_time[i][j]
                model.addConstr(
                    t[j] >= t[i] + service_time[i] + c[i, j] - big_M * (1 - x[i, j]),
                    name=f"time_prop_{i}_{j}"
                )

    # Time window constraints
    for i in nodes:
        model.addConstr(t[i] >= time_window_start[i], name=f"tw_lo_{i}")
        model.addConstr(t[i] <= time_window_end[i], name=f"tw_hi_{i}")

    # Return-to-depot timing constraint
    # When courier goes from i back to depot, the arrival time at depot (end) must be within horizon
    # We use an auxiliary variable for end time at depot
    t_end = model.addVar(lb=0.0, ub=planning_horizon, vtype=GRB.CONTINUOUS, name="t_end")
    for i in clients:
        model.addConstr(
            t_end >= t[i] + service_time[i] + c[i, depot] - big_M * (1 - x[i, depot]),
            name=f"end_time_{i}"
        )
    model.addConstr(t_end <= planning_horizon, name="horizon")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}