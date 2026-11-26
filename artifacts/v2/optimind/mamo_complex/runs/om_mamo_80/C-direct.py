import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs    = params["costs"]
    protein  = params["protein"]
    carbs    = params["carbs"]
    calories = params["calories"]
    req_protein  = params["req_protein"]
    req_carbs    = params["req_carbs"]
    req_calories = params["req_calories"]

    foods = range(len(costs))

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Integer decision variables: number of servings of each food
    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total cost
    model.setObjective(gp.quicksum(costs[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints (meet or exceed daily requirements)
    model.addConstr(gp.quicksum(protein[i]  * x[i] for i in foods) >= req_protein,  "protein")
    model.addConstr(gp.quicksum(carbs[i]    * x[i] for i in foods) >= req_carbs,    "carbs")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= req_calories, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}