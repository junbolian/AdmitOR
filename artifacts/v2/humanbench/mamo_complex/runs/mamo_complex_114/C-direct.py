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

    n_foods = 6
    foods = range(n_foods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req, name="protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carb_req, name="carb_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_req, name="calorie_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}