import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n_items = 11  # structural constant: item_0 through item_10

    model = gp.Model("production_optimization")
    model.Params.OutputFlag = 0

    x = model.addVars(n_items, lb=0.0, name="x")
    for i in range(n_items):
        x[i].ub = production_capacity[i]

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in range(n_items)) <= resource_capacity,
        name="resource_constraint",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}