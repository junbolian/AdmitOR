import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeffs = params["nutrient_coeffs"]
    num_foods = params["num_foods"]
    num_nutrients = params["num_nutrients"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    foods = range(num_foods)
    nutrients = range(num_nutrients)

    x = model.addVars(foods, lb=0.0, name="x")

    model.setObjective(gp.quicksum(costs[j] * x[j] for j in foods), GRB.MINIMIZE)

    for i in nutrients:
        model.addConstr(
            gp.quicksum(nutrient_coeffs[i][j] * x[j] for j in foods) >= nutrient_min[i],
            name=f"nutrient_min_{i}"
        )
        model.addConstr(
            gp.quicksum(nutrient_coeffs[i][j] * x[j] for j in foods) <= nutrient_max[i],
            name=f"nutrient_max_{i}"
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