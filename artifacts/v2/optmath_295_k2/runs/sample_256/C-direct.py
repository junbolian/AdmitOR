import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    factories = range(4)
    months = range(4)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary run decision: run[f, t] = 1 if factory f is active in month t
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")

    # Continuous production level: prod[f, t]
    prod = model.addVars(factories, months, lb=0.0, name="prod")

    # Objective: minimize total activation + production costs
    model.setObjective(
        gp.quicksum(activation_cost[f] * run[f, t] for f in factories for t in months)
        + gp.quicksum(production_cost[f] * prod[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Production bounds linked to run decision
    for f in factories:
        for t in months:
            # prod[f,t] >= min_production[f] * run[f,t]
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t])
            # prod[f,t] <= max_production[f] * run[f,t]
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t])

    # Demand satisfaction per month
    for t in months:
        model.addConstr(gp.quicksum(prod[f, t] for f in factories) >= demand[t])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}