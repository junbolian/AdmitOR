import gurobipy as gp
from gurobipy import GRB

def solve(params):
    base_cost = params["base_cost"]
    per_mw_cost = params["per_mw_cost"]
    startup_cost = params["startup_cost"]
    demand = params["demand"]
    reserve_demand = params["reserve_demand"]
    min_output = params["min_output"]
    max_output = params["max_output"]
    max_generators = params["max_generators"]
    initial_startup_allowance = params["initial_startup_allowance"]

    T = [0, 1, 2]
    P = [0, 1, 2, 3, 4]

    model = gp.Model("power_generation")
    model.Params.OutputFlag = 0

    n = model.addVars(T, P, vtype=GRB.INTEGER, name="n")
    out = model.addVars(T, P, vtype=GRB.CONTINUOUS, lb=0.0, name="out")
    s = model.addVars(T, P, vtype=GRB.INTEGER, lb=0, name="s")

    model.setObjective(
        gp.quicksum(base_cost[t] * n[t, p] for t in T for p in P)
        + gp.quicksum(per_mw_cost[t] * out[t, p] for t in T for p in P)
        + gp.quicksum(startup_cost[t] * s[t, p] for t in T for p in P),
        GRB.MINIMIZE,
    )

    for t in T:
        for p in P:
            model.addConstr(n[t, p] <= max_generators[t])
            model.addConstr(out[t, p] >= min_output[t] * n[t, p])
            model.addConstr(out[t, p] <= max_output[t] * n[t, p])

    for p in P:
        model.addConstr(gp.quicksum(out[t, p] for t in T) >= demand[p])
        model.addConstr(
            gp.quicksum(max_output[t] * n[t, p] for t in T) >= reserve_demand[p]
        )

    for t in T:
        model.addConstr(n[t, 0] <= s[t, 0] + initial_startup_allowance[t])
        for p in P[1:]:
            model.addConstr(n[t, p] <= n[t, p - 1] + s[t, p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}