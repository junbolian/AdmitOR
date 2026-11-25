import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_use = params["resource_use"]
    resource_budget = params["resource_budget"]
    capacity = params["capacity"]

    n_items = 13

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, name="x")

    for i in range(n_items):
        x[i].ub = capacity[i]

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(resource_use[i] * x[i] for i in range(n_items)) <= resource_budget,
        name="resource"
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