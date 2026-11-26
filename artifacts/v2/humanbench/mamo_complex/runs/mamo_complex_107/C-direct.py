import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calorie_req = params["calorie_req"]

    # params are lists indexed by food position
    n_foods = len(cost)
    foods = list(range(n_foods))

    model = gp.Model("diet")
    model.Params.OutputFlag = 0

    x = model.addVars(foods, lb=0.0, vtype=GRB.CONTINUOUS, name="servings")

    model.setObjective(
        gp.quicksum(cost[f] * x[f] for f in foods), GRB.MINIMIZE
    )

    model.addConstr(
        gp.quicksum(protein[f] * x[f] for f in foods) >= protein_req,
        name="protein_min",
    )
    model.addConstr(
        gp.quicksum(carbs[f] * x[f] for f in foods) >= carbs_req,
        name="carbs_min",
    )
    model.addConstr(
        gp.quicksum(calories[f] * x[f] for f in foods) >= calorie_req,
        name="calorie_min",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD, GRB.UNBOUNDED):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}