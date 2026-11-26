import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_grams = params["protein_grams"]
    carb_grams = params["carb_grams"]
    calories = params["calories"]
    prices = params["prices"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    foods = range(len(prices))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(prices[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein_grams[i] * x[i] for i in foods) >= protein_target, "protein")
    model.addConstr(gp.quicksum(carb_grams[i] * x[i] for i in foods) >= carb_target, "carbs")
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