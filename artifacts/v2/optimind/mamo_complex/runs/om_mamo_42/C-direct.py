import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    price = params["price"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    foods = ["Chicken", "Tuna", "Eggs", "Beef", "Rice", "Apples", "Bread"]
    n = len(foods)

    model = gp.Model("meal_plan")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(price[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in range(n)) >= protein_target, "protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in range(n)) >= carb_target, "carb_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in range(n)) >= calorie_target, "calorie_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}