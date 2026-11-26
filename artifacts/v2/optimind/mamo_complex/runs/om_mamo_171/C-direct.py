import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_chicken = params["price_chicken"]
    price_cheese = params["price_cheese"]
    price_rice = params["price_rice"]
    price_beans = params["price_beans"]

    protein_chicken = params["protein_chicken"]
    protein_cheese = params["protein_cheese"]
    protein_rice = params["protein_rice"]
    protein_beans = params["protein_beans"]

    carbs_chicken = params["carbs_chicken"]
    carbs_cheese = params["carbs_cheese"]
    carbs_rice = params["carbs_rice"]
    carbs_beans = params["carbs_beans"]

    calories_chicken = params["calories_chicken"]
    calories_cheese = params["calories_cheese"]
    calories_rice = params["calories_rice"]
    calories_beans = params["calories_beans"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    chicken = model.addVar(lb=0.0, name="chicken")
    cheese = model.addVar(lb=0.0, name="cheese")
    rice = model.addVar(lb=0.0, name="rice")
    beans = model.addVar(lb=0.0, name="beans")

    model.setObjective(
        price_chicken * chicken + price_cheese * cheese + price_rice * rice + price_beans * beans,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * chicken + protein_cheese * cheese + protein_rice * rice + protein_beans * beans >= protein_req,
        "protein"
    )
    model.addConstr(
        carbs_chicken * chicken + carbs_cheese * cheese + carbs_rice * rice + carbs_beans * beans >= carbs_req,
        "carbs"
    )
    model.addConstr(
        calories_chicken * chicken + calories_cheese * cheese + calories_rice * rice + calories_beans * beans >= calories_req,
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