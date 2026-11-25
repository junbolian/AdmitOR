import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n_items = 11
    items = range(n_items)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, lb=0.0, ub=[production_capacity[i] for i in items], name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in items), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in items) <= resource_capacity,
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}