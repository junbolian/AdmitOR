import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    resource_usage = params["resource_usage"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]

    n = len(profit)

    model = gp.Model("production")

    x = model.addVars(n, lb=0.0, ub=capacity, name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_usage[i] * x[i] for i in range(n)) <= resource_budget,
        name="resource_budget",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}