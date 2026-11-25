import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 4
    num_months = 4
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Binary run decision variables
    run = model.addVars(months, factories, vtype=GRB.BINARY, name="run")

    # Continuous production variables
    produce = model.addVars(months, factories, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[t, f] + variable_cost[f] * produce[t, f]
            for t in months for f in factories
        ),
        GRB.MINIMIZE
    )

    # Production bounds linked to run decision
    for t in months:
        for f in factories:
            model.addConstr(produce[t, f] >= min_production[f] * run[t, f], name=f"min_prod_{t}_{f}")
            model.addConstr(produce[t, f] <= max_production[f] * run[t, f], name=f"max_prod_{t}_{f}")

    # Demand satisfaction
    for t in months:
        model.addConstr(
            gp.quicksum(produce[t, f] for f in factories) >= demand[t],
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