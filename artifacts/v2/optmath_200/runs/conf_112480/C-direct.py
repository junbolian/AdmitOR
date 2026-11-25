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

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Binary run decision: run[t, f] = 1 if factory f runs in month t
    run = model.addVars(months, factories, vtype=GRB.BINARY, name="run")

    # Continuous production level: prod[t, f]
    prod = model.addVars(months, factories, lb=0.0, name="prod")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[t, f] + variable_cost[f] * prod[t, f]
                    for t in months for f in factories),
        GRB.MINIMIZE
    )

    # Minimum production if running
    for t in months:
        for f in factories:
            model.addConstr(prod[t, f] >= min_production[f] * run[t, f],
                            name=f"min_prod_{t}_{f}")

    # Maximum production if running
    for t in months:
        for f in factories:
            model.addConstr(prod[t, f] <= max_production[f] * run[t, f],
                            name=f"max_prod_{t}_{f}")

    # Demand satisfaction each month
    for t in months:
        model.addConstr(gp.quicksum(prod[t, f] for f in factories) >= demand[t],
                        name=f"demand_{t}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}