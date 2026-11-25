import gurobipy as gp
from gurobipy import GRB

def solve(params):
    food_cost = params["food_cost"]
    max_buy_per_food = params["max_buy_per_food"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coefficients = params["nutrient_coefficients"]

    num_nutrients = len(nutrient_min)
    num_foods = len(food_cost)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    buy = model.addVars(num_foods, lb=0.0, ub=max_buy_per_food, name="Buy")

    model.setObjective(
        gp.quicksum(food_cost[f] * buy[f] for f in range(num_foods)),
        GRB.MINIMIZE
    )

    for n in range(num_nutrients):
        nutrient_expr = gp.quicksum(
            nutrient_coefficients[n][f] * buy[f] for f in range(num_foods)
        )
        model.addConstr(nutrient_expr >= nutrient_min[n], name=f"nutrient_min_{n}")
        model.addConstr(nutrient_expr <= nutrient_max[n], name=f"nutrient_max_{n}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}