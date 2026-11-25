import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 6
    num_months = 4
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary run decision
    run = model.addVars(months, factories, vtype=GRB.BINARY, name="run")
    # Production level
    produce = model.addVars(months, factories, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[t, f] + variable_cost[f] * produce[t, f]
            for t in months for f in factories
        ),
        GRB.MINIMIZE
    )

    # Production bounds tied to run decision
    for t in months:
        for f in factories:
            model.addConstr(produce[t, f] >= min_production[f] * run[t, f])
            model.addConstr(produce[t, f] <= max_production[f] * run[t, f])

    # Demand satisfaction
    for t in months:
        model.addConstr(gp.quicksum(produce[t, f] for f in factories) >= demand[t])

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