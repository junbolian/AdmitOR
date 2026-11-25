import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit_per_unit"]
    resource_consumption = params["resource_consumption_per_unit"]
    capacity = params["resource_capacity"]
    upper_limits = params["production_upper_limits"]

    n_items = 11
    items = range(n_items)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_items, lb=0.0, ub=[upper_limits[i] for i in items], name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in items), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(resource_consumption[i] * x[i] for i in items) <= capacity,
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