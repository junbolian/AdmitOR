import gurobipy as gp
from gurobipy import GRB

def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    num_factories = 6
    num_months = 6

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="run")
    produce = model.addVars(num_factories, num_months, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[f, t] + variable_cost[f] * produce[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        ),
        GRB.MINIMIZE
    )

    # Minimum production if operational
    for f in range(num_factories):
        for t in range(num_months):
            model.addConstr(
                produce[f, t] >= min_production[f] * run[f, t],
                name=f"min_prod_{f}_{t}"
            )

    # Maximum production if operational
    for f in range(num_factories):
        for t in range(num_months):
            model.addConstr(
                produce[f, t] <= max_production[f] * run[f, t],
                name=f"max_prod_{f}_{t}"
            )

    # Demand satisfaction per month
    for t in range(num_months):
        model.addConstr(
            gp.quicksum(produce[f, t] for f in range(num_factories)) >= demand[t],
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