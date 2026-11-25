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

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    prod = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="prod")

    # Objective: minimize total activation + production costs
    model.setObjective(
        gp.quicksum(activation_cost[f] * run[f, t] + production_cost[f] * prod[f, t]
                    for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Constraints
    for f in factories:
        for t in months:
            # Production lower bound if activated
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t], name=f"min_prod_{f}_{t}")
            # Production upper bound if activated
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t], name=f"max_prod_{f}_{t}")

    for t in months:
        # Demand satisfaction
        model.addConstr(gp.quicksum(prod[f, t] for f in factories) >= demand[t], name=f"demand_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}