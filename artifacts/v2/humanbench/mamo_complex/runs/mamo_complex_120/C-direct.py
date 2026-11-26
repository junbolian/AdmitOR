import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_grams = params["protein_grams"]
    carbs_grams = params["carbs_grams"]
    calories = params["calories"]
    cost = params["cost"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    n = len(cost)
    foods = range(n)

    model = gp.Model("meal_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables: how many units of each food to purchase (continuous >= 0)
    x = model.addVars(foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein_grams[i] * x[i] for i in foods) >= protein_target, "protein")
    model.addConstr(gp.quicksum(carbs_grams[i] * x[i] for i in foods) >= carb_target, "carbs")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_target, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}