import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n_items = 13
    items = list(range(n_items))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {i: model.addVar(lb=0.0, ub=production_capacity[i], name=f"x_{i}") for i in items}

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in items), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_rate[i] * x[i] for i in items) <= resource_capacity,
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