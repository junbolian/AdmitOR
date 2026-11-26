import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_pasta = params["protein_pasta"]
    carb_pasta = params["carb_pasta"]
    cal_pasta = params["cal_pasta"]
    cost_pasta = params["cost_pasta"]

    protein_avocado = params["protein_avocado"]
    carb_avocado = params["carb_avocado"]
    cal_avocado = params["cal_avocado"]
    cost_avocado = params["cost_avocado"]

    protein_chicken = params["protein_chicken"]
    carb_chicken = params["carb_chicken"]
    cal_chicken = params["cal_chicken"]
    cost_chicken = params["cost_chicken"]

    protein_tofu = params["protein_tofu"]
    carb_tofu = params["carb_tofu"]
    cal_tofu = params["cal_tofu"]
    cost_tofu = params["cost_tofu"]

    protein_spinach = params["protein_spinach"]
    carb_spinach = params["carb_spinach"]
    cal_spinach = params["cal_spinach"]
    cost_spinach = params["cost_spinach"]

    protein_cheese = params["protein_cheese"]
    carb_cheese = params["carb_cheese"]
    cal_cheese = params["cal_cheese"]
    cost_cheese = params["cost_cheese"]

    req_protein = params["req_protein"]
    req_carb = params["req_carb"]
    req_cal = params["req_cal"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_pasta = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_pasta")
    x_avocado = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_avocado")
    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_tofu = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_tofu")
    x_spinach = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_spinach")
    x_cheese = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_cheese")

    model.setObjective(
        cost_pasta * x_pasta +
        cost_avocado * x_avocado +
        cost_chicken * x_chicken +
        cost_tofu * x_tofu +
        cost_spinach * x_spinach +
        cost_cheese * x_cheese,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_pasta * x_pasta +
        protein_avocado * x_avocado +
        protein_chicken * x_chicken +
        protein_tofu * x_tofu +
        protein_spinach * x_spinach +
        protein_cheese * x_cheese >= req_protein,
        "protein"
    )

    model.addConstr(
        carb_pasta * x_pasta +
        carb_avocado * x_avocado +
        carb_chicken * x_chicken +
        carb_tofu * x_tofu +
        carb_spinach * x_spinach +
        carb_cheese * x_cheese >= req_carb,
        "carb"
    )

    model.addConstr(
        cal_pasta * x_pasta +
        cal_avocado * x_avocado +
        cal_chicken * x_chicken +
        cal_tofu * x_tofu +
        cal_spinach * x_spinach +
        cal_cheese * x_cheese >= req_cal,
        "calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}