import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(fixed_cost)
    num_months = len(demand)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Binary run decision: run[f, t] = 1 if factory f operates in month t
    run = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="run")

    # Continuous production level: prod[f, t]
    prod = model.addVars(num_factories, num_months, lb=0.0, name="prod")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[f, t] + variable_cost[f] * prod[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        ),
        GRB.MINIMIZE
    )

    # Production bounds linked to run decision
    for f in range(num_factories):
        for t in range(num_months):
            # prod[f,t] >= min_production[f] * run[f,t]
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t], name=f"min_prod_{f}_{t}")
            # prod[f,t] <= max_production[f] * run[f,t]
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t], name=f"max_prod_{f}_{t}")

    # Demand satisfaction per month
    for t in range(num_months):
        model.addConstr(
            gp.quicksum(prod[f, t] for f in range(num_factories)) >= demand[t],
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