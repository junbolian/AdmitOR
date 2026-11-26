import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    foods = range(len(protein))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_target, "protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carb_target, "carb_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_target, "calorie_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}