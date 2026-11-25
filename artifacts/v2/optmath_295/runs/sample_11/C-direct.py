import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    n = len(profit_margins)
    upper_bounds = [float(v) for v in production_capacities]

    model = gp.Model("production")
    model.Params.OutputFlag = 0

    x = model.addVars(n, lb=0.0, ub=upper_bounds, name="x")

    model.setObjective(
        gp.quicksum(float(profit_margins[i]) * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(float(resource_coefficients[i]) * x[i] for i in range(n))
        <= float(resource_capacity),
        name="resource",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "inf_or_unbounded"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"status_{model.Status}"}