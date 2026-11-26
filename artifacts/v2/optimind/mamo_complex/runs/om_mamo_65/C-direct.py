import gurobipy as gp
from gurobipy import GRB

def solve(params):
    lentils_cost = params["lentils_cost"]
    rice_cost = params["rice_cost"]
    chicken_cost = params["chicken_cost"]
    beef_cost = params["beef_cost"]
    tofu_cost = params["tofu_cost"]

    lentils_protein = params["lentils_protein"]
    rice_protein = params["rice_protein"]
    chicken_protein = params["chicken_protein"]
    beef_protein = params["beef_protein"]
    tofu_protein = params["tofu_protein"]

    lentils_carbs = params["lentils_carbs"]
    rice_carbs = params["rice_carbs"]
    chicken_carbs = params["chicken_carbs"]
    beef_carbs = params["beef_carbs"]
    tofu_carbs = params["tofu_carbs"]

    lentils_calories = params["lentils_calories"]
    rice_calories = params["rice_calories"]
    chicken_calories = params["chicken_calories"]
    beef_calories = params["beef_calories"]
    tofu_calories = params["tofu_calories"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_lentils = model.addVar(vtype=GRB.INTEGER, lb=0, name="lentils")
    x_rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="rice")
    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="chicken")
    x_beef = model.addVar(vtype=GRB.INTEGER, lb=0, name="beef")
    x_tofu = model.addVar(vtype=GRB.INTEGER, lb=0, name="tofu")

    model.setObjective(
        lentils_cost * x_lentils + rice_cost * x_rice + chicken_cost * x_chicken +
        beef_cost * x_beef + tofu_cost * x_tofu,
        GRB.MINIMIZE
    )

    model.addConstr(
        lentils_protein * x_lentils + rice_protein * x_rice + chicken_protein * x_chicken +
        beef_protein * x_beef + tofu_protein * x_tofu >= protein_req,
        name="protein"
    )

    model.addConstr(
        lentils_carbs * x_lentils + rice_carbs * x_rice + chicken_carbs * x_chicken +
        beef_carbs * x_beef + tofu_carbs * x_tofu >= carbs_req,
        name="carbs"
    )

    model.addConstr(
        lentils_calories * x_lentils + rice_calories * x_rice + chicken_calories * x_chicken +
        beef_calories * x_beef + tofu_calories * x_tofu >= calories_req,
        name="calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}