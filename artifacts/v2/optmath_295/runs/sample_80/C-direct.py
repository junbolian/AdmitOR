import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n_products = 11
    products = range(n_products)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(products, lb=[min_production[i] for i in products],
                      ub=[max_production[i] for i in products],
                      vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(profit_per_unit[i] * x[i] for i in products), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in products) <= time_capacity,
        name="time_capacity"
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