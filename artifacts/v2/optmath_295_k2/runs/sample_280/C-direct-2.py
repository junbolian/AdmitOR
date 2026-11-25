import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(activation_cost)
    num_months = len(demand)

    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    produce = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total activation + production costs
    model.setObjective(
        gp.quicksum(activation_cost[f] * run[f, t] for f in factories for t in months) +
        gp.quicksum(production_cost[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Constraints
    for f in factories:
        for t in months:
            # If activated, production >= min_production
            model.addConstr(produce[f, t] >= min_production[f] * run[f, t], name=f"min_prod_{f}_{t}")
            # If activated, production <= max_production
            model.addConstr(produce[f, t] <= max_production[f] * run[f, t], name=f"max_prod_{f}_{t}")

    for t in months:
        # Demand satisfaction
        model.addConstr(
            gp.quicksum(produce[f, t] for f in factories) >= demand[t],
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
        return {"objective": None, "status": f"status_{model.Status}"}