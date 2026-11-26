import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_chicken = params["cost_chicken"]
    cost_pasta = params["cost_pasta"]
    cost_apples = params["cost_apples"]
    cost_tuna = params["cost_tuna"]
    cost_rice = params["cost_rice"]

    protein_chicken = params["protein_chicken"]
    protein_pasta = params["protein_pasta"]
    protein_apples = params["protein_apples"]
    protein_tuna = params["protein_tuna"]
    protein_rice = params["protein_rice"]

    carbs_chicken = params["carbs_chicken"]
    carbs_pasta = params["carbs_pasta"]
    carbs_apples = params["carbs_apples"]
    carbs_tuna = params["carbs_tuna"]
    carbs_rice = params["carbs_rice"]

    calories_chicken = params["calories_chicken"]
    calories_pasta = params["calories_pasta"]
    calories_apples = params["calories_apples"]
    calories_tuna = params["calories_tuna"]
    calories_rice = params["calories_rice"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_pasta = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_pasta")
    x_apples = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_apples")
    x_tuna = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_tuna")
    x_rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_rice")

    model.setObjective(
        cost_chicken * x_chicken +
        cost_pasta * x_pasta +
        cost_apples * x_apples +
        cost_tuna * x_tuna +
        cost_rice * x_rice,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_pasta * x_pasta +
        protein_apples * x_apples +
        protein_tuna * x_tuna +
        protein_rice * x_rice >= protein_req,
        "protein"
    )

    model.addConstr(
        carbs_chicken * x_chicken +
        carbs_pasta * x_pasta +
        carbs_apples * x_apples +
        carbs_tuna * x_tuna +
        carbs_rice * x_rice >= carbs_req,
        "carbs"
    )

    model.addConstr(
        calories_chicken * x_chicken +
        calories_pasta * x_pasta +
        calories_apples * x_apples +
        calories_tuna * x_tuna +
        calories_rice * x_rice >= calories_req,
        "calories"
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