import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken  = params["protein_chicken"]
    protein_rice     = params["protein_rice"]
    protein_broccoli = params["protein_broccoli"]
    protein_eggs     = params["protein_eggs"]

    carbs_chicken    = params["carbs_chicken"]
    carbs_rice       = params["carbs_rice"]
    carbs_broccoli   = params["carbs_broccoli"]
    carbs_eggs       = params["carbs_eggs"]

    calories_chicken  = params["calories_chicken"]
    calories_rice     = params["calories_rice"]
    calories_broccoli = params["calories_broccoli"]
    calories_eggs     = params["calories_eggs"]

    price_chicken    = params["price_chicken"]
    price_rice       = params["price_rice"]
    price_broccoli   = params["price_broccoli"]
    price_eggs       = params["price_eggs"]

    protein_req  = params["protein_requirement"]
    carbs_req    = params["carbs_requirement"]
    calories_req = params["calories_requirement"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    chicken  = model.addVar(vtype=GRB.INTEGER, lb=0, name="chicken")
    rice     = model.addVar(vtype=GRB.INTEGER, lb=0, name="rice")
    broccoli = model.addVar(vtype=GRB.INTEGER, lb=0, name="broccoli")
    eggs     = model.addVar(vtype=GRB.INTEGER, lb=0, name="eggs")

    model.setObjective(
        price_chicken * chicken + price_rice * rice +
        price_broccoli * broccoli + price_eggs * eggs,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_chicken * chicken + protein_rice * rice +
        protein_broccoli * broccoli + protein_eggs * eggs >= protein_req,
        name="protein"
    )
    model.addConstr(
        carbs_chicken * chicken + carbs_rice * rice +
        carbs_broccoli * broccoli + carbs_eggs * eggs >= carbs_req,
        name="carbs"
    )
    model.addConstr(
        calories_chicken * chicken + calories_rice * rice +
        calories_broccoli * broccoli + calories_eggs * eggs >= calories_req,
        name="calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}