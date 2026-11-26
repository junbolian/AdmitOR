import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_bread = params["protein_bread"]
    carbs_bread = params["carbs_bread"]
    calories_bread = params["calories_bread"]
    cost_bread = params["cost_bread"]

    protein_milk = params["protein_milk"]
    carbs_milk = params["carbs_milk"]
    calories_milk = params["calories_milk"]
    cost_milk = params["cost_milk"]

    protein_fish = params["protein_fish"]
    carbs_fish = params["carbs_fish"]
    calories_fish = params["calories_fish"]
    cost_fish = params["cost_fish"]

    protein_potato = params["protein_potato"]
    carbs_potato = params["carbs_potato"]
    calories_potato = params["calories_potato"]
    cost_potato = params["cost_potato"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    bread = model.addVar(lb=0.0, name="bread")
    milk = model.addVar(lb=0.0, name="milk")
    fish = model.addVar(lb=0.0, name="fish")
    potato = model.addVar(lb=0.0, name="potato")

    model.setObjective(
        cost_bread * bread + cost_milk * milk + cost_fish * fish + cost_potato * potato,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_bread * bread + protein_milk * milk + protein_fish * fish + protein_potato * potato >= protein_req,
        "protein"
    )
    model.addConstr(
        carbs_bread * bread + carbs_milk * milk + carbs_fish * fish + carbs_potato * potato >= carbs_req,
        "carbs"
    )
    model.addConstr(
        calories_bread * bread + calories_milk * milk + calories_fish * fish + calories_potato * potato >= calories_req,
        "calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        raw_obj = model.ObjVal
        rounded_obj = round(raw_obj)
        return {"objective": float(rounded_obj), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}