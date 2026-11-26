import gurobipy as gp
from gurobipy import GRB

def solve(params):
    foods = ["chicken", "rice", "apples", "cheese", "tofu"]
    protein = {f: params[f"protein_{f}"] for f in foods}
    carb = {f: params[f"carb_{f}"] for f in foods}
    cal = {f: params[f"cal_{f}"] for f in foods}
    cost = {f: params[f"cost_{f}"] for f in foods}

    model = gp.Model("diet")
    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[f] * x[f] for f in foods) >= params["protein_req"], "protein")
    model.addConstr(gp.quicksum(carb[f] * x[f] for f in foods) >= params["carb_req"], "carb")
    model.addConstr(gp.quicksum(cal[f] * x[f] for f in foods) >= params["cal_req"], "cal")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no optimal solution"}