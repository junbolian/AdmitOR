import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    n = len(cost)
    foods = range(n)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Integer variables: portions of each food item
    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_requirement, "protein")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carb_requirement, "carbs")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_requirement, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}