import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 6
    num_months = 5
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: activate factory f in month t
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    # Continuous: production level of factory f in month t
    prod = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="prod")

    # Objective: minimize activation + production costs
    model.setObjective(
        gp.quicksum(activation_cost[f] * run[f, t] for f in factories for t in months)
        + gp.quicksum(production_cost[f] * prod[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Min production if activated
    for f in factories:
        for t in months:
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t], name=f"min_prod_{f}_{t}")

    # Max production if activated
    for f in factories:
        for t in months:
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t], name=f"max_prod_{f}_{t}")

    # Demand satisfaction
    for t in months:
        model.addConstr(
            gp.quicksum(prod[f, t] for f in factories) >= demand[t],
            name=f"demand_{t}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}