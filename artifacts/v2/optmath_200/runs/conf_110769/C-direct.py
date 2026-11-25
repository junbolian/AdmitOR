import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    var_cost = params["var_cost"]
    min_prod = params["min_prod"]
    max_capacity = params["max_capacity"]
    demand = params["demand"]

    num_factories = 4
    num_months = 4
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(months, factories, vtype=GRB.BINARY, name="run")
    produce = model.addVars(months, factories, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[t, f] + var_cost[f] * produce[t, f]
                    for t in months for f in factories),
        GRB.MINIMIZE
    )

    # Minimum production if running
    for t in months:
        for f in factories:
            model.addConstr(produce[t, f] >= min_prod[f] * run[t, f],
                            name=f"min_prod_{t}_{f}")

    # Maximum production if running
    for t in months:
        for f in factories:
            model.addConstr(produce[t, f] <= max_capacity[f] * run[t, f],
                            name=f"max_prod_{t}_{f}")

    # Demand satisfaction
    for t in months:
        model.addConstr(gp.quicksum(produce[t, f] for f in factories) >= demand[t],
                        name=f"demand_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}