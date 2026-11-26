import gurobipy as gp
from gurobipy import GRB

def solve(params):
    foods = ["chicken", "oats", "tofu", "rice", "beef", "salmon"]

    protein = {f: params[f"protein_{f}"] for f in foods}
    carbs = {f: params[f"carbs_{f}"] for f in foods}
    calories = {f: params[f"calories_{f}"] for f in foods}
    cost = {f: params[f"cost_{f}"] for f in foods}

    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[f] * x[f] for f in foods) >= protein_target, "protein")
    model.addConstr(gp.quicksum(carbs[f] * x[f] for f in foods) >= carb_target, "carbs")
    model.addConstr(gp.quicksum(calories[f] * x[f] for f in foods) >= calorie_target, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}