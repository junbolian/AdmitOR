import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 5
    num_months = 4
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Binary: 1 if factory f is operational in month t
    operate = model.addVars(factories, months, vtype=GRB.BINARY, name="operate")

    # Continuous: units produced by factory f in month t
    produce = model.addVars(factories, months, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * operate[f, t] for f in factories for t in months)
        + gp.quicksum(variable_cost[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Min production: produce[f,t] >= min_production[f] * operate[f,t]
    model.addConstrs(
        (produce[f, t] >= min_production[f] * operate[f, t]
         for f in factories for t in months),
        name="min_prod"
    )

    # Max production: produce[f,t] <= max_production[f] * operate[f,t]
    model.addConstrs(
        (produce[f, t] <= max_production[f] * operate[f, t]
         for f in factories for t in months),
        name="max_prod"
    )

    # Demand satisfaction: sum of production across factories >= demand[t]
    model.addConstrs(
        (gp.quicksum(produce[f, t] for f in factories) >= demand[t]
         for t in months),
        name="demand"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}