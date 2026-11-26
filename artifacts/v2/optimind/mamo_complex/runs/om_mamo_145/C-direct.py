import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_eggs = params["protein_eggs"]
    carb_eggs = params["carb_eggs"]
    cal_eggs = params["cal_eggs"]
    cost_eggs = params["cost_eggs"]

    protein_rice = params["protein_rice"]
    carb_rice = params["carb_rice"]
    cal_rice = params["cal_rice"]
    cost_rice = params["cost_rice"]

    protein_chicken = params["protein_chicken"]
    carb_chicken = params["carb_chicken"]
    cal_chicken = params["cal_chicken"]
    cost_chicken = params["cost_chicken"]

    protein_broccoli = params["protein_broccoli"]
    carb_broccoli = params["carb_broccoli"]
    cal_broccoli = params["cal_broccoli"]
    cost_broccoli = params["cost_broccoli"]

    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    cal_req = params["cal_req"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    eggs = model.addVar(vtype=GRB.INTEGER, lb=0, name="eggs")
    rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="rice")
    chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="chicken")
    broccoli = model.addVar(vtype=GRB.INTEGER, lb=0, name="broccoli")

    model.setObjective(
        cost_eggs * eggs + cost_rice * rice + cost_chicken * chicken + cost_broccoli * broccoli,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_eggs * eggs + protein_rice * rice + protein_chicken * chicken + protein_broccoli * broccoli >= protein_req,
        "protein"
    )
    model.addConstr(
        carb_eggs * eggs + carb_rice * rice + carb_chicken * chicken + carb_broccoli * broccoli >= carb_req,
        "carb"
    )
    model.addConstr(
        cal_eggs * eggs + cal_rice * rice + cal_chicken * chicken + cal_broccoli * broccoli >= cal_req,
        "calorie"
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