import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    protein_coeffs = params["protein_coeffs"]
    carb_coeffs = params["carb_coeffs"]
    calorie_coeffs = params["calorie_coeffs"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    n_foods = len(costs)

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    servings = model.addVars(n_foods, lb=0.0, name="servings")

    model.setObjective(
        gp.quicksum(costs[i] * servings[i] for i in range(n_foods)),
        GRB.MINIMIZE
    )

    model.addConstr(
        gp.quicksum(protein_coeffs[i] * servings[i] for i in range(n_foods)) >= protein_requirement,
        name="protein"
    )
    model.addConstr(
        gp.quicksum(carb_coeffs[i] * servings[i] for i in range(n_foods)) >= carb_requirement,
        name="carbs"
    )
    model.addConstr(
        gp.quicksum(calorie_coeffs[i] * servings[i] for i in range(n_foods)) >= calorie_requirement,
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