import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_bread = params["protein_bread"]
    carb_bread = params["carb_bread"]
    cal_bread = params["cal_bread"]
    cost_bread = params["cost_bread"]

    protein_milk = params["protein_milk"]
    carb_milk = params["carb_milk"]
    cal_milk = params["cal_milk"]
    cost_milk = params["cost_milk"]

    protein_fish = params["protein_fish"]
    carb_fish = params["carb_fish"]
    cal_fish = params["cal_fish"]
    cost_fish = params["cost_fish"]

    protein_potato = params["protein_potato"]
    carb_potato = params["carb_potato"]
    cal_potato = params["cal_potato"]
    cost_potato = params["cost_potato"]

    req_protein = params["req_protein"]
    req_carb = params["req_carb"]
    req_cal = params["req_cal"]

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
        protein_bread * bread + protein_milk * milk + protein_fish * fish + protein_potato * potato >= req_protein,
        name="protein_req"
    )
    model.addConstr(
        carb_bread * bread + carb_milk * milk + carb_fish * fish + carb_potato * potato >= req_carb,
        name="carb_req"
    )
    model.addConstr(
        cal_bread * bread + cal_milk * milk + cal_fish * fish + cal_potato * potato >= req_cal,
        name="cal_req"
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