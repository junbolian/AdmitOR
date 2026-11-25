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
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary run decision
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    # Production quantity
    produce = model.addVars(factories, months, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[f, t] for f in factories for t in months)
        + gp.quicksum(variable_cost[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Min production when running
    for f in factories:
        for t in months:
            model.addConstr(produce[f, t] >= min_production[f] * run[f, t])

    # Max production when running
    for f in factories:
        for t in months:
            model.addConstr(produce[f, t] <= max_production[f] * run[f, t])

    # Demand satisfaction
    for t in months:
        model.addConstr(gp.quicksum(produce[f, t] for f in factories) >= demand[t])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}