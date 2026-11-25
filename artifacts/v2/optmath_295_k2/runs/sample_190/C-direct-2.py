import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    food_max_purchase = params["food_max_purchase"]
    nutrient_contribution = params["nutrient_contribution"]

    n_foods = 25
    n_nutrients = 7

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    buy = model.addVars(n_foods, lb=0.0, ub=food_max_purchase, name="Buy")

    model.setObjective(
        gp.quicksum(cost[f] * buy[f] for f in range(n_foods)),
        GRB.MINIMIZE
    )

    for n in range(n_nutrients):
        nutrient_total = gp.quicksum(nutrient_contribution[n][f] * buy[f] for f in range(n_foods))
        model.addConstr(nutrient_total >= nutrient_min[n], name=f"nutrient_min_{n}")
        model.addConstr(nutrient_total <= nutrient_max[n], name=f"nutrient_max_{n}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}