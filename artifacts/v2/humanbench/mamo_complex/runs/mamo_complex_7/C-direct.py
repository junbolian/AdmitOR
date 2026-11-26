import gurobipy as gp
from gurobipy import GRB

def solve(params):
    foods = ["Chicken", "Rice", "Vegetables", "Bread", "Almonds", "Salmon"]
    n = len(foods)

    protein_list = params["protein"]
    carbs_list = params["carbs"]
    calories_list = params["calories"]
    cost_list = params["cost"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = gp.Model("meal_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost_list[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein_list[i] * x[i] for i in range(n)) >= protein_requirement, "protein_req")
    model.addConstr(gp.quicksum(carbs_list[i] * x[i] for i in range(n)) >= carb_requirement, "carb_req")
    model.addConstr(gp.quicksum(calories_list[i] * x[i] for i in range(n)) >= calorie_requirement, "calorie_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}