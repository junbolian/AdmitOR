import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    capacity = params["resource_availability"]
    limits = params["production_limit"]

    n = 45
    items = list(range(n))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {i: model.addVar(lb=0.0, ub=limits[i], name=f"x_{i}") for i in items}

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in items),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(consumption[i] * x[i] for i in items) <= capacity,
        name="resource"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}