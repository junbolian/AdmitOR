import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_steak = params["cost_steak"]
    cost_rice = params["cost_rice"]
    cost_chicken = params["cost_chicken"]
    cost_lettuce = params["cost_lettuce"]
    cost_almonds = params["cost_almonds"]

    protein_steak = params["protein_steak"]
    protein_rice = params["protein_rice"]
    protein_chicken = params["protein_chicken"]
    protein_lettuce = params["protein_lettuce"]
    protein_almonds = params["protein_almonds"]

    carbs_steak = params["carbs_steak"]
    carbs_rice = params["carbs_rice"]
    carbs_chicken = params["carbs_chicken"]
    carbs_lettuce = params["carbs_lettuce"]
    carbs_almonds = params["carbs_almonds"]

    calories_steak = params["calories_steak"]
    calories_rice = params["calories_rice"]
    calories_chicken = params["calories_chicken"]
    calories_lettuce = params["calories_lettuce"]
    calories_almonds = params["calories_almonds"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_steak = model.addVar(lb=0.0, name="x_steak")
    x_rice = model.addVar(lb=0.0, name="x_rice")
    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_lettuce = model.addVar(lb=0.0, name="x_lettuce")
    x_almonds = model.addVar(lb=0.0, name="x_almonds")

    model.setObjective(
        cost_steak * x_steak +
        cost_rice * x_rice +
        cost_chicken * x_chicken +
        cost_lettuce * x_lettuce +
        cost_almonds * x_almonds,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_steak * x_steak +
        protein_rice * x_rice +
        protein_chicken * x_chicken +
        protein_lettuce * x_lettuce +
        protein_almonds * x_almonds >= protein_req,
        name="protein"
    )

    model.addConstr(
        carbs_steak * x_steak +
        carbs_rice * x_rice +
        carbs_chicken * x_chicken +
        carbs_lettuce * x_lettuce +
        carbs_almonds * x_almonds >= carbs_req,
        name="carbs"
    )

    model.addConstr(
        calories_steak * x_steak +
        calories_rice * x_rice +
        calories_chicken * x_chicken +
        calories_lettuce * x_lettuce +
        calories_almonds * x_almonds >= calories_req,
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