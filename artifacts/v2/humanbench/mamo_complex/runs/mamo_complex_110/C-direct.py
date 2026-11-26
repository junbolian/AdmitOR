import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_eggs = params["cost_eggs"]
    cost_rice = params["cost_rice"]
    cost_chicken = params["cost_chicken"]
    cost_broccoli = params["cost_broccoli"]

    protein_eggs = params["protein_eggs"]
    protein_rice = params["protein_rice"]
    protein_chicken = params["protein_chicken"]
    protein_broccoli = params["protein_broccoli"]

    carbs_eggs = params["carbs_eggs"]
    carbs_rice = params["carbs_rice"]
    carbs_chicken = params["carbs_chicken"]
    carbs_broccoli = params["carbs_broccoli"]

    cal_eggs = params["cal_eggs"]
    cal_rice = params["cal_rice"]
    cal_chicken = params["cal_chicken"]
    cal_broccoli = params["cal_broccoli"]

    req_protein = params["req_protein"]
    req_carbs = params["req_carbs"]
    req_cal = params["req_cal"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    eggs = model.addVar(lb=0.0, name="eggs")
    rice = model.addVar(lb=0.0, name="rice")
    chicken = model.addVar(lb=0.0, name="chicken")
    broccoli = model.addVar(lb=0.0, name="broccoli")

    model.setObjective(
        cost_eggs * eggs + cost_rice * rice + cost_chicken * chicken + cost_broccoli * broccoli,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_eggs * eggs + protein_rice * rice + protein_chicken * chicken + protein_broccoli * broccoli >= req_protein,
        "protein"
    )
    model.addConstr(
        carbs_eggs * eggs + carbs_rice * rice + carbs_chicken * chicken + carbs_broccoli * broccoli >= req_carbs,
        "carbs"
    )
    model.addConstr(
        cal_eggs * eggs + cal_rice * rice + cal_chicken * chicken + cal_broccoli * broccoli >= req_cal,
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