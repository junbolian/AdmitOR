import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    n_foods = len(cost)
    foods = range(n_foods)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Decision variables: how many units of each food to purchase (continuous, non-negative)
    x = model.addVars(foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req, "protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= carbs_req, "carbs_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calories_req, "calories_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}