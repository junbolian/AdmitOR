import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    var_cost = params["var_cost"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]
    demand = params["demand"]

    num_factories = 4
    num_months = 6

    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    produce = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[f, t] + var_cost[f] * produce[f, t]
                    for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Production bounds linked to run decision
    for f in factories:
        for t in months:
            # produce[f,t] >= min_prod[f] * run[f,t]
            model.addConstr(produce[f, t] >= min_prod[f] * run[f, t], name=f"min_prod_{f}_{t}")
            # produce[f,t] <= max_prod[f] * run[f,t]
            model.addConstr(produce[f, t] <= max_prod[f] * run[f, t], name=f"max_prod_{f}_{t}")

    # Demand satisfaction
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
        return {"objective": None, "status": f"status_{model.Status}"}