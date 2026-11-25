import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]   # list of length 5
    var_cost   = params["var_cost"]     # list of length 5
    min_prod   = params["min_prod"]     # list of length 5
    max_prod   = params["max_prod"]     # list of length 5
    demand     = params["demand"]       # list of length 4

    num_factories = 5
    num_months    = 4
    factories = range(num_factories)
    months    = range(num_months)

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Binary: operate factory f in month t
    operate = model.addVars(factories, months, vtype=GRB.BINARY, name="operate")

    # Continuous: units produced by factory f in month t
    produce = model.addVars(factories, months, lb=0.0, vtype=GRB.CONTINUOUS, name="produce")

    # Objective: minimize total fixed + variable cost
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * operate[f, t] + var_cost[f] * produce[f, t]
            for f in factories for t in months
        ),
        GRB.MINIMIZE
    )

    # Minimum production if operating
    for f in factories:
        for t in months:
            model.addConstr(
                produce[f, t] >= min_prod[f] * operate[f, t],
                name=f"min_prod_{f}_{t}"
            )

    # Maximum production if operating
    for f in factories:
        for t in months:
            model.addConstr(
                produce[f, t] <= max_prod[f] * operate[f, t],
                name=f"max_prod_{f}_{t}"
            )

    # Demand satisfaction each month
    for t in months:
        model.addConstr(
            gp.quicksum(produce[f, t] for f in factories) >= demand[t],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}