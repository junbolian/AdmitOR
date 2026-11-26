import gurobipy as gp
from gurobipy import GRB

def solve(params):
    target_N = params["target_N"]
    target_P = params["target_P"]
    target_K = params["target_K"]
    tol = params["tol"]
    price = params["price"]        # list indexed 0..4 (fertilizers 1..5)
    nutrient_N = params["nutrient_N"]
    nutrient_P = params["nutrient_P"]
    nutrient_K = params["nutrient_K"]

    # Use 0-based indices to match list indexing
    fertilizers = range(5)

    model = gp.Model("fertilizer_mix")
    model.setParam("OutputFlag", 0)

    # x[i] = fraction of fertilizer i in the blend (fractions sum to 1)
    x = {i: model.addVar(lb=0.0, name=f"x_{i}") for i in fertilizers}

    # Blend fractions must sum to 1 (cost per 100 lb of mix)
    model.addConstr(gp.quicksum(x[i] for i in fertilizers) == 1.0, name="sum_to_one")

    # Nitrogen: at least target_N%, no more than target_N + tol %
    model.addConstr(
        gp.quicksum(nutrient_N[i] * x[i] for i in fertilizers) >= target_N,
        name="N_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_N[i] * x[i] for i in fertilizers) <= target_N + tol,
        name="N_upper"
    )

    # Phosphorus: at least target_P%, no more than target_P + tol %
    model.addConstr(
        gp.quicksum(nutrient_P[i] * x[i] for i in fertilizers) >= target_P,
        name="P_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_P[i] * x[i] for i in fertilizers) <= target_P + tol,
        name="P_upper"
    )

    # Potash: at least target_K%, no more than target_K + tol %
    model.addConstr(
        gp.quicksum(nutrient_K[i] * x[i] for i in fertilizers) >= target_K,
        name="K_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_K[i] * x[i] for i in fertilizers) <= target_K + tol,
        name="K_upper"
    )

    # Minimize cost per 100 lb of blend
    model.setObjective(
        gp.quicksum(price[i] * x[i] for i in fertilizers),
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