import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_content = params["protein_content"]   # list of 4 values
    carb_content = params["carb_content"]          # list of 4 values
    calorie_content = params["calorie_content"]    # list of 4 values
    cost_per_unit = params["cost_per_unit"]        # list of 4 values
    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    foods = range(4)  # bread, milk, fish, potato

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each food to consume (continuous, non-negative)
    x = model.addVars(foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost_per_unit[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_req, "protein")
    model.addConstr(gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_req, "carb")
    model.addConstr(gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_req, "calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}