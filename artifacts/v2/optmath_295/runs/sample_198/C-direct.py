import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    consumption = params["consumption"]
    capacity = params["capacity"]
    upper_limit = params["upper_limit"]

    n_items = 20

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, name="x")
    for i in range(n_items):
        x[i].ub = upper_limit[i]

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n_items)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(consumption[i] * x[i] for i in range(n_items)) <= capacity,
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
        return {"objective": None, "status": f"status_{model.Status}"}