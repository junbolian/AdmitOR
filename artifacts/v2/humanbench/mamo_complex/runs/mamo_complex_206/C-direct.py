import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nutrient_A_grain1 = params["nutrient_A_grain1"]
    nutrient_B_grain1 = params["nutrient_B_grain1"]
    nutrient_C_grain1 = params["nutrient_C_grain1"]
    nutrient_D_grain1 = params["nutrient_D_grain1"]
    cost_grain1 = params["cost_grain1"]

    nutrient_A_grain2 = params["nutrient_A_grain2"]
    nutrient_B_grain2 = params["nutrient_B_grain2"]
    nutrient_C_grain2 = params["nutrient_C_grain2"]
    nutrient_D_grain2 = params["nutrient_D_grain2"]
    cost_grain2 = params["cost_grain2"]

    nutrient_A_grain3 = params["nutrient_A_grain3"]
    nutrient_B_grain3 = params["nutrient_B_grain3"]
    nutrient_C_grain3 = params["nutrient_C_grain3"]
    nutrient_D_grain3 = params["nutrient_D_grain3"]
    cost_grain3 = params["cost_grain3"]

    req_A = params["req_nutrient_A"]
    req_B = params["req_nutrient_B"]
    req_C = params["req_nutrient_C"]
    req_D = params["req_nutrient_D"]

    model = gp.Model("sheep_diet")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(lb=0.0, name="x1")  # pounds of Grain 1
    x2 = model.addVar(lb=0.0, name="x2")  # pounds of Grain 2
    x3 = model.addVar(lb=0.0, name="x3")  # pounds of Grain 3

    model.setObjective(cost_grain1 * x1 + cost_grain2 * x2 + cost_grain3 * x3, GRB.MINIMIZE)

    model.addConstr(nutrient_A_grain1 * x1 + nutrient_A_grain2 * x2 + nutrient_A_grain3 * x3 >= req_A, "nutrient_A")
    model.addConstr(nutrient_B_grain1 * x1 + nutrient_B_grain2 * x2 + nutrient_B_grain3 * x3 >= req_B, "nutrient_B")
    model.addConstr(nutrient_C_grain1 * x1 + nutrient_C_grain2 * x2 + nutrient_C_grain3 * x3 >= req_C, "nutrient_C")
    model.addConstr(nutrient_D_grain1 * x1 + nutrient_D_grain2 * x2 + nutrient_D_grain3 * x3 >= req_D, "nutrient_D")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}