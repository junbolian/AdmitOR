import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    food_cost = params["food_cost"]
    protein_target = params["protein_target"]
    carb_target = params["carb_target"]
    calorie_target = params["calorie_target"]

    n_foods = 5
    foods = range(n_foods)

    model = gp.Model("weekly_meal_plan")
    model.setParam("OutputFlag", 0)

    # Integer portions of each food
    x = model.addVars(n_foods, vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total cost
    model.setObjective(
        gp.quicksum(food_cost[i] * x[i] for i in foods),
        GRB.MINIMIZE
    )

    # Nutritional requirements
    model.addConstr(
        gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_target,
        name="protein"
    )
    model.addConstr(
        gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_target,
        name="carb"
    )
    model.addConstr(
        gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_target,
        name="calorie"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}