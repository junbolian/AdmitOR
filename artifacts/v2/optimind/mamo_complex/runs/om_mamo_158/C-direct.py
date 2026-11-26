import gurobipy as gp
from gurobipy import GRB


def solve(params):
    foods = ["chicken", "rice", "veg", "bread", "almonds", "salmon"]

    protein = {f: params[f"protein_{f}"] for f in foods}
    carb = {f: params[f"carb_{f}"] for f in foods}
    cal = {f: params[f"cal_{f}"] for f in foods}
    cost = {f: params[f"cost_{f}"] for f in foods}

    model = gp.Model("meal_planning")
    model.ModelSense = GRB.MINIMIZE

    servings = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="servings")

    model.setObjective(gp.quicksum(cost[f] * servings[f] for f in foods), GRB.MINIMIZE)

    model.addConstr(
        gp.quicksum(protein[f] * servings[f] for f in foods)
        >= params["protein_target"], "protein_min"
    )
    model.addConstr(
        gp.quicksum(carb[f] * servings[f] for f in foods)
        >= params["carb_target"], "carb_min"
    )
    model.addConstr(
        gp.quicksum(cal[f] * servings[f] for f in foods)
        >= params["cal_target"], "cal_min"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}