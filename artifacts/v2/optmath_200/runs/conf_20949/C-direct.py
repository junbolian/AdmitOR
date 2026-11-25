import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 6
    num_months = 5

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="run")
    production = model.addVars(num_factories, num_months, vtype=GRB.CONTINUOUS, lb=0.0, name="production")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[f, t] + variable_cost[f] * production[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        ),
        GRB.MINIMIZE
    )

    # Constraints
    for f in range(num_factories):
        for t in range(num_months):
            # Production >= min_production * run
            model.addConstr(production[f, t] >= min_production[f] * run[f, t])
            # Production <= max_production * run
            model.addConstr(production[f, t] <= max_production[f] * run[f, t])

    for t in range(num_months):
        model.addConstr(
            gp.quicksum(production[f, t] for f in range(num_factories)) >= demand[t]
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