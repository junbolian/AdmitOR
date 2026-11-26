import gurobipy as gp
from gurobipy import GRB

def solve(params):
    calories = params["calories"]
    chocolate = params["chocolate"]
    sugar = params["sugar"]
    fat = params["fat"]
    cost = params["cost"]
    min_calories = params["min_calories"]
    min_chocolate = params["min_chocolate"]
    min_sugar = params["min_sugar"]
    min_fat = params["min_fat"]

    n_foods = len(calories)
    foods = range(n_foods)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= min_calories, "cal")
    model.addConstr(gp.quicksum(chocolate[i] * x[i] for i in foods) >= min_chocolate, "choc")
    model.addConstr(gp.quicksum(sugar[i] * x[i] for i in foods) >= min_sugar, "sugar")
    model.addConstr(gp.quicksum(fat[i] * x[i] for i in foods) >= min_fat, "fat")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}