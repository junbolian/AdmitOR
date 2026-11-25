import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    variable_costs = params["variable_costs"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 5
    num_months = 6
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary run decision: run[f, t] = 1 if factory f operates in month t
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")

    # Continuous production level
    produce = model.addVars(factories, months, lb=0.0, name="produce")

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_costs[f] * run[f, t] for f in factories for t in months)
        + gp.quicksum(variable_costs[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Production bounds tied to run decision
    for f in factories:
        for t in months:
            # produce >= min_production * run
            model.addConstr(produce[f, t] >= min_production[f] * run[f, t])
            # produce <= max_production * run
            model.addConstr(produce[f, t] <= max_production[f] * run[f, t])

    # Demand satisfaction
    for t in months:
        model.addConstr(
            gp.quicksum(produce[f, t] for f in factories) >= demand[t]
        )

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