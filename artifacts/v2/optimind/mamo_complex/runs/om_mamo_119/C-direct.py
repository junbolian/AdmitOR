import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_per_unit = params["cost_per_unit"]
    protein_per_unit = params["protein_per_unit"]
    carbs_per_unit = params["carbs_per_unit"]
    calories_per_unit = params["calories_per_unit"]
    min_protein = params["min_protein"]
    min_carbs = params["min_carbs"]
    min_calories = params["min_calories"]

    foods = range(len(cost_per_unit))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(cost_per_unit[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein_per_unit[i] * x[i] for i in foods) >= min_protein, name="protein")
    model.addConstr(gp.quicksum(carbs_per_unit[i] * x[i] for i in foods) >= min_carbs, name="carbs")
    model.addConstr(gp.quicksum(calories_per_unit[i] * x[i] for i in foods) >= min_calories, name="calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}