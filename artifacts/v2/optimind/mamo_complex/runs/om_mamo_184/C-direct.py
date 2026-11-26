import gurobipy as gp
from gurobipy import GRB

def solve(params):
    calories_per_food = params["calories_per_food"]
    chocolate_per_food = params["chocolate_per_food"]
    sugar_per_food = params["sugar_per_food"]
    fat_per_food = params["fat_per_food"]
    cost_per_food = params["cost_per_food"]
    min_calories = params["min_calories"]
    min_chocolate = params["min_chocolate"]
    min_sugar = params["min_sugar"]
    min_fat = params["min_fat"]

    n_foods = 4  # brownie, ice cream, cola, cheesecake
    foods = range(n_foods)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Integer variables: units of each food consumed
    x = model.addVars(n_foods, vtype=GRB.INTEGER, lb=0.0, name="x")

    # Objective: minimize total cost (in cents)
    model.setObjective(
        gp.quicksum(cost_per_food[i] * x[i] for i in foods),
        GRB.MINIMIZE
    )

    # Nutritional constraints
    model.addConstr(
        gp.quicksum(calories_per_food[i] * x[i] for i in foods) >= min_calories,
        name="calories"
    )
    model.addConstr(
        gp.quicksum(chocolate_per_food[i] * x[i] for i in foods) >= min_chocolate,
        name="chocolate"
    )
    model.addConstr(
        gp.quicksum(sugar_per_food[i] * x[i] for i in foods) >= min_sugar,
        name="sugar"
    )
    model.addConstr(
        gp.quicksum(fat_per_food[i] * x[i] for i in foods) >= min_fat,
        name="fat"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        # Return cost in dollars (cost_per_food is in cents)
        return {"objective": model.ObjVal / 100.0, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}