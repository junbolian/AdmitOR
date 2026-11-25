import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_margin = params["profit_margin"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n_items = len(profit_margin)

    model = gp.Model("production_optimization")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, name="x")

    for i in range(n_items):
        x[i].ub = production_limit[i]

    model.setObjective(
        gp.quicksum(profit_margin[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n_items)) <= resource_capacity,
        name="resource_capacity"
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