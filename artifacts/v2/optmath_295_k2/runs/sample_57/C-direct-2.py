import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n_items = 44

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, ub=[production_limit[i] for i in range(n_items)], name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n_items)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_rate[i] * x[i] for i in range(n_items)) <= resource_capacity,
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