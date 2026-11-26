import gurobipy as gp
from gurobipy import GRB

def solve(params):
    target_Ni = params["target_Ni"]
    target_Ph = params["target_Ph"]
    target_Po = params["target_Po"]
    tol_Ni = params["tol_Ni"]
    tol_Ph = params["tol_Ph"]
    tol_Po = params["tol_Po"]
    nutrient_Ni = params["nutrient_Ni"]  # list of length 5, 0-indexed
    nutrient_Ph = params["nutrient_Ph"]
    nutrient_Po = params["nutrient_Po"]
    price = params["price"]

    fertilizers = range(1, 6)

    model = gp.Model("fertilizer_mix")
    model.setParam("OutputFlag", 0)

    # x[i] = fraction of fertilizer i in the mix (fractions sum to 1)
    x = {}
    for i in fertilizers:
        x[i] = model.addVar(lb=0.0, ub=1.0, name=f"x_{i}")

    # Fractions must sum to 1
    model.addConstr(gp.quicksum(x[i] for i in fertilizers) == 1.0, name="sum_to_one")

    # Nitrogen: target <= blend_Ni <= target + tol
    model.addConstr(
        gp.quicksum(nutrient_Ni[i - 1] * x[i] for i in fertilizers) >= target_Ni,
        name="Ni_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_Ni[i - 1] * x[i] for i in fertilizers) <= target_Ni + tol_Ni,
        name="Ni_upper"
    )

    # Phosphorus: target <= blend_Ph <= target + tol
    model.addConstr(
        gp.quicksum(nutrient_Ph[i - 1] * x[i] for i in fertilizers) >= target_Ph,
        name="Ph_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_Ph[i - 1] * x[i] for i in fertilizers) <= target_Ph + tol_Ph,
        name="Ph_upper"
    )

    # Potash: target <= blend_Po <= target + tol
    model.addConstr(
        gp.quicksum(nutrient_Po[i - 1] * x[i] for i in fertilizers) >= target_Po,
        name="Po_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_Po[i - 1] * x[i] for i in fertilizers) <= target_Po + tol_Po,
        name="Po_upper"
    )

    # Objective: minimize cost per 100 pounds
    model.setObjective(
        gp.quicksum(price[i - 1] * x[i] for i in fertilizers),
        GRB.MINIMIZE
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