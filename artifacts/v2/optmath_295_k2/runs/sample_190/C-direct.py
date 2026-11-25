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

    # Resolve per-food upper bound: accept either a scalar (applies to all
    # foods) or an explicit list/array of length n_foods.
    try:
        scalar_ub = float(food_max_purchase)
        ub_list = [scalar_ub] * n_foods
    except (TypeError, ValueError):
        ub_list = [float(v) for v in food_max_purchase]
        if len(ub_list) != n_foods:
            raise ValueError(
                "food_max_purchase must be a scalar or have length %d" % n_foods
            )

    model = gp.Model("diet")
    model.Params.OutputFlag = 0

    buy = model.addVars(n_foods, lb=0.0, ub=ub_list, name="Buy")

    model.setObjective(
        gp.quicksum(float(cost[i]) * buy[i] for i in range(n_foods)),
        GRB.MINIMIZE,
    )

    for n in range(n_nutrients):
        row = nutrient_contribution[n]
        total = gp.quicksum(float(row[f]) * buy[f] for f in range(n_foods))
        model.addConstr(total >= float(nutrient_min[n]), name=f"nutrient_min_{n}")
        model.addConstr(total <= float(nutrient_max[n]), name=f"nutrient_max_{n}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}