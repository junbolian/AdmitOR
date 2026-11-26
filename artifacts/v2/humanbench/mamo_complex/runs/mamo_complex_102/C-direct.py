import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = [
        params["cost_food1"],
        params["cost_food2"],
        params["cost_food3"],
        params["cost_food4"],
    ]
    protein = [
        params["protein_food1"],
        params["protein_food2"],
        params["protein_food3"],
        params["protein_food4"],
    ]
    carb = [
        params["carb_food1"],
        params["carb_food2"],
        params["carb_food3"],
        params["carb_food4"],
    ]
    calories = [
        params["calories_food1"],
        params["calories_food2"],
        params["calories_food3"],
        params["calories_food4"],
    ]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    foods = range(4)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req, "protein")
    model.addConstr(gp.quicksum(carb[i] * x[i] for i in foods) >= carb_req, "carb")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_req, "calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}