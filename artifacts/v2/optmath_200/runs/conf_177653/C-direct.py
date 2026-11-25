import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    F = range(len(fixed_cost))
    T = range(len(demand))

    model = gp.Model("multi_factory_production")
    model.Params.OutputFlag = 0

    run = model.addVars(F, T, vtype=GRB.BINARY, name="run")
    prod = model.addVars(F, T, lb=0.0, vtype=GRB.CONTINUOUS, name="prod")

    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[f, t] for f in F for t in T)
        + gp.quicksum(variable_cost[f] * prod[f, t] for f in F for t in T),
        GRB.MINIMIZE,
    )

    for f in F:
        for t in T:
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t], name=f"cap_{f}_{t}")
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t], name=f"min_{f}_{t}")

    for t in T:
        model.addConstr(gp.quicksum(prod[f, t] for f in F) >= demand[t], name=f"demand_{t}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}