import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeff = params["nutrient_coeff"]

    n_foods = 24
    n_nutrients = 11

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_foods, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[j] * x[j] for j in range(n_foods)),
        GRB.MINIMIZE
    )

    for i in range(n_nutrients):
        nutrient_expr = gp.quicksum(nutrient_coeff[i][j] * x[j] for j in range(n_foods))
        model.addConstr(nutrient_expr >= nutrient_min[i], name=f"nut_min_{i}")
        model.addConstr(nutrient_expr <= nutrient_max[i], name=f"nut_max_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}