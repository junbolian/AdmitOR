import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_chicken = params["cost_chicken"]
    cost_rice = params["cost_rice"]
    cost_broccoli = params["cost_broccoli"]
    cost_tofu = params["cost_tofu"]
    cost_beans = params["cost_beans"]

    protein_chicken = params["protein_chicken"]
    protein_rice = params["protein_rice"]
    protein_broccoli = params["protein_broccoli"]
    protein_tofu = params["protein_tofu"]
    protein_beans = params["protein_beans"]

    carb_chicken = params["carb_chicken"]
    carb_rice = params["carb_rice"]
    carb_broccoli = params["carb_broccoli"]
    carb_tofu = params["carb_tofu"]
    carb_beans = params["carb_beans"]

    cal_chicken = params["cal_chicken"]
    cal_rice = params["cal_rice"]
    cal_broccoli = params["cal_broccoli"]
    cal_tofu = params["cal_tofu"]
    cal_beans = params["cal_beans"]

    req_protein = params["req_protein"]
    req_carb = params["req_carb"]
    req_cal = params["req_cal"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_rice")
    x_broccoli = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_broccoli")
    x_tofu = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_tofu")
    x_beans = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_beans")

    model.setObjective(
        cost_chicken * x_chicken +
        cost_rice * x_rice +
        cost_broccoli * x_broccoli +
        cost_tofu * x_tofu +
        cost_beans * x_beans,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_rice * x_rice +
        protein_broccoli * x_broccoli +
        protein_tofu * x_tofu +
        protein_beans * x_beans >= req_protein,
        name="protein"
    )

    model.addConstr(
        carb_chicken * x_chicken +
        carb_rice * x_rice +
        carb_broccoli * x_broccoli +
        carb_tofu * x_tofu +
        carb_beans * x_beans >= req_carb,
        name="carb"
    )

    model.addConstr(
        cal_chicken * x_chicken +
        cal_rice * x_rice +
        cal_broccoli * x_broccoli +
        cal_tofu * x_tofu +
        cal_beans * x_beans >= req_cal,
        name="calories"
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