import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    protein_rice = params["protein_rice"]
    protein_broccoli = params["protein_broccoli"]
    protein_eggs = params["protein_eggs"]

    carbs_chicken = params["carbs_chicken"]
    carbs_rice = params["carbs_rice"]
    carbs_broccoli = params["carbs_broccoli"]
    carbs_eggs = params["carbs_eggs"]

    calories_chicken = params["calories_chicken"]
    calories_rice = params["calories_rice"]
    calories_broccoli = params["calories_broccoli"]
    calories_eggs = params["calories_eggs"]

    cost_chicken = params["cost_chicken"]
    cost_rice = params["cost_rice"]
    cost_broccoli = params["cost_broccoli"]
    cost_eggs = params["cost_eggs"]

    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    chicken = model.addVar(lb=0.0, name="chicken")
    rice = model.addVar(lb=0.0, name="rice")
    broccoli = model.addVar(lb=0.0, name="broccoli")
    eggs = model.addVar(lb=0.0, name="eggs")

    model.setObjective(
        cost_chicken * chicken + cost_rice * rice + cost_broccoli * broccoli + cost_eggs * eggs,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * chicken + protein_rice * rice + protein_broccoli * broccoli + protein_eggs * eggs >= protein_requirement,
        "protein"
    )
    model.addConstr(
        carbs_chicken * chicken + carbs_rice * rice + carbs_broccoli * broccoli + carbs_eggs * eggs >= carb_requirement,
        "carbs"
    )
    model.addConstr(
        calories_chicken * chicken + calories_rice * rice + calories_broccoli * broccoli + calories_eggs * eggs >= calorie_requirement,
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