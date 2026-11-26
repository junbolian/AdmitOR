import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    cost = params["cost"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    cal_req = params["cal_req"]

    n_foods = 5
    foods = range(n_foods)

    model = gp.Model("meal_prep")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req, "protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carb_req, "carb_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= cal_req, "cal_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}