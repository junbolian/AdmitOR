import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    req_protein_1 = params["req_protein_1"]
    req_protein_2 = params["req_protein_2"]
    req_calories = params["req_calories"]

    n = len(cost)
    foods = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= req_protein_1, name="protein_req_1")
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= req_protein_2, name="protein_req_2")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= req_calories, name="calories_req")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}