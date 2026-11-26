import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    n_foods = 8
    foods = range(n_foods)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity of each food (continuous, non-negative)
    x = model.addVars(n_foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= req_protein, "protein_req")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in foods) >= req_carbs, "carbs_req")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= req_calories, "calories_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}