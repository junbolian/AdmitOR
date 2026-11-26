import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req_1 = params["protein_req_1"]
    protein_req_2 = params["protein_req_2"]
    calorie_req = params["calorie_req"]

    n_foods = len(cost)
    foods = range(n_foods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req_1, name="protein1")
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req_2, name="protein2")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_req, name="calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}