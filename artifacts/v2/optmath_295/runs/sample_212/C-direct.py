import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    resource_limit = params["resource_limit"]
    capacity = params["capacity"]

    n = 43

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, name="x")

    for i in range(n):
        x[i].ub = capacity[i]

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_coeff[i] * x[i] for i in range(n)) <= resource_limit,
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