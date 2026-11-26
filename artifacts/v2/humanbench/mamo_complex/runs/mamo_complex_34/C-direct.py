import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    carbs_chicken = params["carbs_chicken"]
    calories_chicken = params["calories_chicken"]
    cost_chicken = params["cost_chicken"]

    protein_tofu = params["protein_tofu"]
    carbs_tofu = params["carbs_tofu"]
    calories_tofu = params["calories_tofu"]
    cost_tofu = params["cost_tofu"]

    protein_rice = params["protein_rice"]
    carbs_rice = params["carbs_rice"]
    calories_rice = params["calories_rice"]
    cost_rice = params["cost_rice"]

    protein_avocado = params["protein_avocado"]
    carbs_avocado = params["carbs_avocado"]
    calories_avocado = params["calories_avocado"]
    cost_avocado = params["cost_avocado"]

    protein_min = params["protein_min"]
    carbs_min = params["carbs_min"]
    calories_min = params["calories_min"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_tofu = model.addVar(lb=0.0, name="x_tofu")
    x_rice = model.addVar(lb=0.0, name="x_rice")
    x_avocado = model.addVar(lb=0.0, name="x_avocado")

    model.setObjective(
        cost_chicken * x_chicken +
        cost_tofu * x_tofu +
        cost_rice * x_rice +
        cost_avocado * x_avocado,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * x_chicken +
        protein_tofu * x_tofu +
        protein_rice * x_rice +
        protein_avocado * x_avocado >= protein_min,
        "protein_req"
    )

    model.addConstr(
        carbs_chicken * x_chicken +
        carbs_tofu * x_tofu +
        carbs_rice * x_rice +
        carbs_avocado * x_avocado >= carbs_min,
        "carbs_req"
    )

    model.addConstr(
        calories_chicken * x_chicken +
        calories_tofu * x_tofu +
        calories_rice * x_rice +
        calories_avocado * x_avocado >= calories_min,
        "calories_req"
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