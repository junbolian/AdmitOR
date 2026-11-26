import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    n = len(cost)
    foods = list(range(n))

    model = gp.Model("meal_prep")
    model.Params.OutputFlag = 0

    buy = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="buy")

    model.setObjective(
        gp.quicksum(cost[j] * buy[j] for j in foods), GRB.MINIMIZE
    )

    model.addConstr(
        gp.quicksum(protein[j] * buy[j] for j in foods) >= protein_req,
        "protein_min",
    )
    model.addConstr(
        gp.quicksum(carbs[j] * buy[j] for j in foods) >= carb_req,
        "carbs_min",
    )
    model.addConstr(
        gp.quicksum(calories[j] * buy[j] for j in foods) >= calorie_req,
        "calories_min",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}