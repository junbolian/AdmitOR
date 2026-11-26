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
    foods = range(n)

    model = gp.Model("meal_prep")
    model.setParam("OutputFlag", 0)

    # Integer portions of each food item
    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total cost
    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req, "protein")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carb_req, "carbs")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_req, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}