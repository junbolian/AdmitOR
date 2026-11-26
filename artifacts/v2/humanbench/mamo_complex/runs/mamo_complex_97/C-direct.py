import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]
    cost = params["cost"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]

    n_foods = 8
    foods = range(n_foods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_req, "protein")
    model.addConstr(gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_req, "carbs")
    model.addConstr(gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_req, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}