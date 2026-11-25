import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_margin = params["profit_margin"]
    time_per_unit = params["time_per_unit"]
    capacity_hours = params["capacity_hours"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n_products = 12

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_products, lb=[min_production[i] for i in range(n_products)],
                      ub=[max_production[i] for i in range(n_products)],
                      vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(
        gp.quicksum(profit_margin[i] * x[i] for i in range(n_products)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n_products)) <= capacity_hours,
        name="capacity"
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