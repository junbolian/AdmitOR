import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    num_factories = params["num_factories"]
    num_months = params["num_months"]

    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: activate factory f in month t
    activate = model.addVars(factories, months, vtype=GRB.BINARY, name="activate")

    # Continuous: production level of factory f in month t
    produce = model.addVars(factories, months, lb=0.0, name="produce")

    # Objective: minimize total activation + production cost
    model.setObjective(
        gp.quicksum(activation_cost[f] * activate[f, t] for f in factories for t in months)
        + gp.quicksum(production_cost[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Production bounds tied to activation
    for f in factories:
        for t in months:
            # produce >= min_production * activate
            model.addConstr(produce[f, t] >= min_production[f] * activate[f, t])
            # produce <= max_production * activate
            model.addConstr(produce[f, t] <= max_production[f] * activate[f, t])

    # Demand satisfaction
    for t in months:
        model.addConstr(gp.quicksum(produce[f, t] for f in factories) >= demand[t])

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