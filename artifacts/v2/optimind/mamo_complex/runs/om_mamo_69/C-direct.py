import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_steak = params["protein_steak"]
    protein_eggs = params["protein_eggs"]
    protein_pasta = params["protein_pasta"]
    protein_chicken = params["protein_chicken"]

    carbs_steak = params["carbs_steak"]
    carbs_eggs = params["carbs_eggs"]
    carbs_pasta = params["carbs_pasta"]
    carbs_chicken = params["carbs_chicken"]

    calories_steak = params["calories_steak"]
    calories_eggs = params["calories_eggs"]
    calories_pasta = params["calories_pasta"]
    calories_chicken = params["calories_chicken"]

    cost_steak = params["cost_steak"]
    cost_eggs = params["cost_eggs"]
    cost_pasta = params["cost_pasta"]
    cost_chicken = params["cost_chicken"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model("meal_plan")
    model.setParam("OutputFlag", 0)

    steak = model.addVar(lb=0.0, name="steak")
    eggs = model.addVar(lb=0.0, name="eggs")
    pasta = model.addVar(lb=0.0, name="pasta")
    chicken = model.addVar(lb=0.0, name="chicken")

    model.setObjective(
        cost_steak * steak + cost_eggs * eggs + cost_pasta * pasta + cost_chicken * chicken,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_steak * steak + protein_eggs * eggs + protein_pasta * pasta + protein_chicken * chicken >= protein_req,
        "protein"
    )
    model.addConstr(
        carbs_steak * steak + carbs_eggs * eggs + carbs_pasta * pasta + carbs_chicken * chicken >= carbs_req,
        "carbs"
    )
    model.addConstr(
        calories_steak * steak + calories_eggs * eggs + calories_pasta * pasta + calories_chicken * chicken >= calories_req,
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