import gurobipy as gp
from gurobipy import GRB

def solve(params):
    food_cost = params["food_cost"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    n_foods = 8  # structural constant: number of food items
    foods = range(n_foods)

    model = gp.Model("diet_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each food item to purchase (continuous, non-negative)
    x = model.addVars(foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(food_cost[i] * x[i] for i in foods),
        GRB.MINIMIZE
    )

    # Nutritional constraints
    model.addConstr(
        gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_requirement,
        name="protein"
    )
    model.addConstr(
        gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_requirement,
        name="carbs"
    )
    model.addConstr(
        gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_requirement,
        name="calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}