import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    capacity = params["resource_capacity"]
    upper_bounds = params["production_upper_bounds"]

    n = 25

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, ub=[upper_bounds[i] for i in range(n)], name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(consumption[i] * x[i] for i in range(n)) <= capacity,
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