import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_lentils = params["cost_lentils"]
    cost_rice = params["cost_rice"]
    cost_chicken = params["cost_chicken"]
    cost_beef = params["cost_beef"]
    cost_tofu = params["cost_tofu"]

    protein_lentils = params["protein_lentils"]
    protein_rice = params["protein_rice"]
    protein_chicken = params["protein_chicken"]
    protein_beef = params["protein_beef"]
    protein_tofu = params["protein_tofu"]

    carbs_lentils = params["carbs_lentils"]
    carbs_rice = params["carbs_rice"]
    carbs_chicken = params["carbs_chicken"]
    carbs_beef = params["carbs_beef"]
    carbs_tofu = params["carbs_tofu"]

    calories_lentils = params["calories_lentils"]
    calories_rice = params["calories_rice"]
    calories_chicken = params["calories_chicken"]
    calories_beef = params["calories_beef"]
    calories_tofu = params["calories_tofu"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calorie_req = params["calorie_req"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_lentils = model.addVar(lb=0.0, name="x_lentils")
    x_rice = model.addVar(lb=0.0, name="x_rice")
    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_beef = model.addVar(lb=0.0, name="x_beef")
    x_tofu = model.addVar(lb=0.0, name="x_tofu")

    model.setObjective(
        cost_lentils * x_lentils +
        cost_rice * x_rice +
        cost_chicken * x_chicken +
        cost_beef * x_beef +
        cost_tofu * x_tofu,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_lentils * x_lentils +
        protein_rice * x_rice +
        protein_chicken * x_chicken +
        protein_beef * x_beef +
        protein_tofu * x_tofu >= protein_req,
        name="protein"
    )

    model.addConstr(
        carbs_lentils * x_lentils +
        carbs_rice * x_rice +
        carbs_chicken * x_chicken +
        carbs_beef * x_beef +
        carbs_tofu * x_tofu >= carbs_req,
        name="carbs"
    )

    model.addConstr(
        calories_lentils * x_lentils +
        calories_rice * x_rice +
        calories_chicken * x_chicken +
        calories_beef * x_beef +
        calories_tofu * x_tofu >= calorie_req,
        name="calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}