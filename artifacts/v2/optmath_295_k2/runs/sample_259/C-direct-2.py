import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]

    n_products = len(profit)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_products, lb=[min_prod[i] for i in range(n_products)],
                      ub=[max_prod[i] for i in range(n_products)],
                      vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(profit[i] * x[i] for i in range(n_products)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n_products)) <= time_capacity,
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