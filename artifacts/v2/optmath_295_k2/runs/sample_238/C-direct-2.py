import gurobipy as gp
from gurobipy import GRB

def solve(params):
    food_cost = params["food_cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    num_foods = params["num_foods"]
    num_nutrients = params["num_nutrients"]

    nutrient_coeffs = []
    for n in range(num_nutrients):
        nutrient_coeffs.append(params[f"nutrient_{n}_coeff"])

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    foods = range(num_foods)
    nutrients = range(num_nutrients)

    x = model.addVars(num_foods, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(food_cost[f] * x[f] for f in foods),
        GRB.MINIMIZE
    )

    for n in nutrients:
        nutrient_expr = gp.quicksum(nutrient_coeffs[n][f] * x[f] for f in foods)
        model.addConstr(nutrient_expr >= nutrient_min[n], name=f"min_nutrient_{n}")
        model.addConstr(nutrient_expr <= nutrient_max[n], name=f"max_nutrient_{n}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}