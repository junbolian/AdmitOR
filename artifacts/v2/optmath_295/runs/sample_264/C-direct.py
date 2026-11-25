import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 4
    num_months = 5
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    produce = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[f, m] + variable_cost[f] * produce[f, m]
                    for f in factories for m in months),
        GRB.MINIMIZE
    )

    # Minimum production if operational
    for f in factories:
        for m in months:
            model.addConstr(produce[f, m] >= min_production[f] * run[f, m],
                            name=f"min_prod_f{f}_m{m}")

    # Maximum production if operational
    for f in factories:
        for m in months:
            model.addConstr(produce[f, m] <= max_production[f] * run[f, m],
                            name=f"max_prod_f{f}_m{m}")

    # Demand satisfaction each month
    for m in months:
        model.addConstr(
            gp.quicksum(produce[f, m] for f in factories) >= demand[m],
            name=f"demand_m{m}"
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