import gurobipy as gp
from gurobipy import GRB

def solve(params):
    chicken_cost = params["chicken_cost"]
    tofu_cost = params["tofu_cost"]
    brown_rice_cost = params["brown_rice_cost"]
    fish_cost = params["fish_cost"]
    lentils_cost = params["lentils_cost"]
    quinoa_cost = params["quinoa_cost"]
    eggs_cost = params["eggs_cost"]
    beef_cost = params["beef_cost"]
    beans_cost = params["beans_cost"]

    protein_per_item = params["protein_per_item"]
    carbs_per_item = params["carbs_per_item"]
    calories_per_item = params["calories_per_item"]

    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    costs = [
        chicken_cost, tofu_cost, brown_rice_cost, fish_cost, lentils_cost,
        quinoa_cost, eggs_cost, beef_cost, beans_cost
    ]

    n = 9
    items = range(n)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(costs[i] * x[i] for i in items), GRB.MINIMIZE)

    model.addConstr(
        gp.quicksum(protein_per_item[i] * x[i] for i in items) >= protein_req,
        name="protein"
    )
    model.addConstr(
        gp.quicksum(carbs_per_item[i] * x[i] for i in items) >= carbs_req,
        name="carbs"
    )
    model.addConstr(
        gp.quicksum(calories_per_item[i] * x[i] for i in items) >= calories_req,
        name="calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}