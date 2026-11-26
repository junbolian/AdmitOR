import gurobipy as gp
from gurobipy import GRB

def solve(params):
    foods = ["Chicken", "Pasta", "Rice", "Beans", "Cheese"]

    protein = {f: params[f"protein_{f}"] for f in foods}
    carbs = {f: params[f"carbs_{f}"] for f in foods}
    calories = {f: params[f"calories_{f}"] for f in foods}
    cost = {f: params[f"cost_{f}"] for f in foods}

    protein_req = params["protein_requirement"]
    carbs_req = params["carbs_requirement"]
    calories_req = params["calories_requirement"]

    model = gp.Model("diet")
    model.Params.OutputFlag = 0

    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.addConstr(
        gp.quicksum(protein[f] * x[f] for f in foods) >= protein_req, "protein"
    )
    model.addConstr(
        gp.quicksum(carbs[f] * x[f] for f in foods) >= carbs_req, "carbs"
    )
    model.addConstr(
        gp.quicksum(calories[f] * x[f] for f in foods) >= calories_req, "calories"
    )

    model.setObjective(gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"failed: status {model.Status}"}