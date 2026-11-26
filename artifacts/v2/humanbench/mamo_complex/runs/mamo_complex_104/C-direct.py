import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    food_price = params["food_price"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    n_foods = len(food_price)
    foods = range(n_foods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, lb=0.0, name="x")

    model.setObjective(gp.quicksum(food_price[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_requirement, "protein")
    model.addConstr(gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_requirement, "carb")
    model.addConstr(gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_requirement, "calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}