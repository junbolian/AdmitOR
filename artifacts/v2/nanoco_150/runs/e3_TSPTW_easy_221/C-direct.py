import gurobipy as gp
from gurobipy import GRB

def solve(params):
    travel = [params[f"travel_time_{i}"] for i in range(8)]
    w_start = [params[f"window_{i}_start"] for i in range(8)]
    w_end   = [params[f"window_{i}_end"]   for i in range(8)]
    horizon      = params["horizon"]
    service_time = params["service_time"]
    n = params["num_nodes"]       # 8
    H = params["num_hospitals"]   # 7

    nodes      = list(range(n))        # 0..7
    hospitals  = list(range(1, n))     # 1..7

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = 1 if van travels directly from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # t[i] = arrival time at node i
    t = model.addVars(nodes, lb=0.0, ub=horizon, vtype=GRB.CONTINUOUS, name="t")

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0)

    # Objective: minimize total travel time
    model.setObjective(
        gp.quicksum(travel[i][j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    # Leave hub exactly once
    model.addConstr(gp.quicksum(x[0, j] for j in hospitals) == 1)
    # Return to hub exactly once
    model.addConstr(gp.quicksum(x[i, 0] for i in hospitals) == 1)

    # Each hospital visited exactly once (one incoming, one outgoing arc)
    for h in hospitals:
        model.addConstr(gp.quicksum(x[i, h] for i in nodes if i != h) == 1)
        model.addConstr(gp.quicksum(x[h, j] for j in nodes if j != h) == 1)

    # Depart hub within its window
    model.addConstr(t[0] >= w_start[0])
    model.addConstr(t[0] <= w_end[0])

    # Time window constraints at hospitals
    for h in hospitals:
        model.addConstr(t[h] >= w_start[h])
        model.addConstr(t[h] <= w_end[h])

    # Subtour elimination via arrival-time propagation (MTZ-style with big-M)
    # If x[i,j]=1 then t[j] >= t[i] + service_time + travel[i][j]
    big_M = horizon + max(travel[i][j] for i in nodes for j in nodes) + service_time
    for i in nodes:
        for j in hospitals:
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + service_time + travel[i][j]
                            - big_M * (1 - x[i, j])
                )

    # Route must finish back at hub within horizon
    # arrival at hub on return = t[0] + travel from last hospital
    # Encode return time via an auxiliary variable
    t_return = model.addVar(lb=0.0, ub=horizon, vtype=GRB.CONTINUOUS, name="t_return")
    for i in hospitals:
        model.addConstr(
            t_return >= t[i] + service_time + travel[i][0]
                        - big_M * (1 - x[i, 0])
        )
    model.addConstr(t_return <= horizon)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}