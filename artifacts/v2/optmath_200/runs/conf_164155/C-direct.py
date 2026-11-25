import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]

    n_items = 40
    items = range(n_items)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, lb=0.0, ub=[capacity[i] for i in items], name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in items), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(resource_coeff[i] * x[i] for i in items) <= resource_budget, name="resource")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}