import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    price = params["price"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    items = ["Chicken", "Pasta", "Apples", "Tuna", "Rice"]
    n = len(items)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(price[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in range(n)) >= protein_requirement, "protein")
    model.addConstr(gp.quicksum(carbs[i] * x[i] for i in range(n)) >= carb_requirement, "carbs")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in range(n)) >= calorie_requirement, "calories")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}