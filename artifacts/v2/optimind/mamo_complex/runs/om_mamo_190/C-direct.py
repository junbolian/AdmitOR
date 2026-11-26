import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_chicken = params["cost_chicken"]
    cost_broccoli = params["cost_broccoli"]
    cost_beef = params["cost_beef"]
    cost_rice = params["cost_rice"]

    protein_chicken = params["protein_chicken"]
    protein_broccoli = params["protein_broccoli"]
    protein_beef = params["protein_beef"]
    protein_rice = params["protein_rice"]

    carbs_chicken = params["carbs_chicken"]
    carbs_broccoli = params["carbs_broccoli"]
    carbs_beef = params["carbs_beef"]
    carbs_rice = params["carbs_rice"]

    calories_chicken = params["calories_chicken"]
    calories_broccoli = params["calories_broccoli"]
    calories_beef = params["calories_beef"]
    calories_rice = params["calories_rice"]

    protein_target = params["protein_target"]
    carbs_target = params["carbs_target"]
    calories_target = params["calories_target"]

    model = gp.Model("meal_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer portions of each food
    x_chicken = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_chicken")
    x_broccoli = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_broccoli")
    x_beef = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_beef")
    x_rice = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_rice")

    # Objective: minimize total cost
    model.setObjective(
        cost_chicken * x_chicken
        + cost_broccoli * x_broccoli
        + cost_beef * x_beef
        + cost_rice * x_rice,
        GRB.MINIMIZE,
    )

    # Nutritional constraints
    model.addConstr(
        protein_chicken * x_chicken
        + protein_broccoli * x_broccoli
        + protein_beef * x_beef
        + protein_rice * x_rice
        >= protein_target,
        name="protein_req",
    )

    model.addConstr(
        carbs_chicken * x_chicken
        + carbs_broccoli * x_broccoli
        + carbs_beef * x_beef
        + carbs_rice * x_rice
        >= carbs_target,
        name="carbs_req",
    )

    model.addConstr(
        calories_chicken * x_chicken
        + calories_broccoli * x_broccoli
        + calories_beef * x_beef
        + calories_rice * x_rice
        >= calories_target,
        name="calories_req",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}