import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # 2D: [factory][month]
    variable_cost = params["variable_cost"] # 1D: [factory]
    min_production = params["min_production"] # 2D: [factory][month]
    max_production = params["max_production"] # 2D: [factory][month]
    demand = params["demand"]              # 1D: [month]

    num_factories = len(variable_cost)
    num_months = len(demand)

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="run")
    production = model.addVars(num_factories, num_months, lb=0.0, name="production")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f][t] * run[f, t] for f in range(num_factories) for t in range(num_months))
        + gp.quicksum(variable_cost[f] * production[f, t] for f in range(num_factories) for t in range(num_months)),
        GRB.MINIMIZE
    )

    # Constraints
    for f in range(num_factories):
        for t in range(num_months):
            # Production >= min_production * run
            model.addConstr(production[f, t] >= min_production[f][t] * run[f, t],
                            name=f"min_prod_{f}_{t}")
            # Production <= max_production * run
            model.addConstr(production[f, t] <= max_production[f][t] * run[f, t],
                            name=f"max_prod_{f}_{t}")

    for t in range(num_months):
        # Total production meets demand
        model.addConstr(
            gp.quicksum(production[f, t] for f in range(num_factories)) >= demand[t],
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