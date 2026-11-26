import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    carb_chicken = params["carb_chicken"]
    cal_chicken = params["cal_chicken"]
    cost_chicken = params["cost_chicken"]

    protein_rice = params["protein_rice"]
    carb_rice = params["carb_rice"]
    cal_rice = params["cal_rice"]
    cost_rice = params["cost_rice"]

    protein_lentils = params["protein_lentils"]
    carb_lentils = params["carb_lentils"]
    cal_lentils = params["cal_lentils"]
    cost_lentils = params["cost_lentils"]

    protein_apples = params["protein_apples"]
    carb_apples = params["carb_apples"]
    cal_apples = params["cal_apples"]
    cost_apples = params["cost_apples"]

    protein_eggs = params["protein_eggs"]
    carb_eggs = params["carb_eggs"]
    cal_eggs = params["cal_eggs"]
    cost_eggs = params["cost_eggs"]

    protein_broccoli = params["protein_broccoli"]
    carb_broccoli = params["carb_broccoli"]
    cal_broccoli = params["cal_broccoli"]
    cost_broccoli = params["cost_broccoli"]

    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_calories = params["req_calories"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_rice = model.addVar(lb=0.0, name="x_rice")
    x_lentils = model.addVar(lb=0.0, name="x_lentils")
    x_apples = model.addVar(lb=0.0, name="x_apples")
    x_eggs = model.addVar(lb=0.0, name="x_eggs")
    x_broccoli = model.addVar(lb=0.0, name="x_broccoli")

    model.setObjective(
        cost_chicken * x_chicken +
        cost_rice * x_rice +
        cost_lentils * x_lentils +
        cost_apples * x_apples +
        cost_eggs * x_eggs +
        cost_broccoli * x_broccoli,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_rice * x_rice +
        protein_lentils * x_lentils +
        protein_apples * x_apples +
        protein_eggs * x_eggs +
        protein_broccoli * x_broccoli >= req_protein,
        name="protein_req"
    )

    model.addConstr(
        carb_chicken * x_chicken +
        carb_rice * x_rice +
        carb_lentils * x_lentils +
        carb_apples * x_apples +
        carb_eggs * x_eggs +
        carb_broccoli * x_broccoli >= req_carbs,
        name="carbs_req"
    )

    model.addConstr(
        cal_chicken * x_chicken +
        cal_rice * x_rice +
        cal_lentils * x_lentils +
        cal_apples * x_apples +
        cal_eggs * x_eggs +
        cal_broccoli * x_broccoli >= req_calories,
        name="calories_req"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}