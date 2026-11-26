import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_per_serving  = params["protein_per_serving"]
    carb_per_serving     = params["carb_per_serving"]
    calories_per_serving = params["calories_per_serving"]
    cost_per_serving     = params["cost_per_serving"]
    protein_requirement  = params["protein_requirement"]
    carb_requirement     = params["carb_requirement"]
    calorie_requirement  = params["calorie_requirement"]

    foods = ["Steak", "Tofu", "Chicken", "Broccoli", "Rice", "Spinach"]
    n = len(foods)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Integer servings (problem says "integral portions")
    x = model.addVars(n, vtype=GRB.INTEGER, lb=0.0, name="x")

    # Objective: minimize cost
    model.setObjective(
        gp.quicksum(cost_per_serving[i] * x[i] for i in range(n)),
        GRB.MINIMIZE
    )

    # Nutritional constraints
    model.addConstr(
        gp.quicksum(protein_per_serving[i]  * x[i] for i in range(n)) >= protein_requirement,
        "protein"
    )
    model.addConstr(
        gp.quicksum(carb_per_serving[i]     * x[i] for i in range(n)) >= carb_requirement,
        "carbs"
    )
    model.addConstr(
        gp.quicksum(calories_per_serving[i] * x[i] for i in range(n)) >= calorie_requirement,
        "calories"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}