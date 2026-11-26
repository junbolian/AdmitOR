import gurobipy as gp
from gurobipy import GRB


def solve(params):
    foods = ["steak", "eggs", "pasta", "chicken"]

    cost = {f: params["cost_" + f] for f in foods}
    protein = {f: params["protein_" + f] for f in foods}
    carbs = {f: params["carbs_" + f] for f in foods}
    calories = {f: params["calories_" + f] for f in foods}

    model = gp.Model("diet")
    model.Params.OutputFlag = 0

    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[f] * x[f] for f in foods) >= params["protein_req"], name="protein")
    model.addConstr(gp.quicksum(carbs[f] * x[f] for f in foods) >= params["carbs_req"], name="carbs")
    model.addConstr(gp.quicksum(calories[f] * x[f] for f in foods) >= params["calories_req"], name="calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": "status_" + str(model.Status)}