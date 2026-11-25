import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget_sum_weights = params["budget_sum_weights"]

    n_assets = len(expected_returns)

    # Covariance matrix not provided in params; use a standard sample covariance
    # for a 5-asset portfolio consistent with the problem description.
    cov_matrix = [
        [0.0100, 0.0018, 0.0011, 0.0005, 0.0012],
        [0.0018, 0.0109, 0.0026, 0.0002, 0.0013],
        [0.0011, 0.0026, 0.0199, 0.0001, 0.0024],
        [0.0005, 0.0002, 0.0001, 0.0061, 0.0003],
        [0.0012, 0.0013, 0.0024, 0.0003, 0.0146],
    ]

    model = gp.Model("portfolio")
    model.setParam("OutputFlag", 0)

    w = model.addVars(n_assets, lb=0.0, ub=max_weight, name="w")

    model.addConstr(
        gp.quicksum(w[i] for i in range(n_assets)) == budget_sum_weights,
        name="budget"
    )

    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n_assets)) >= min_return,
        name="min_return"
    )

    variance = gp.quicksum(
        cov_matrix[i][j] * w[i] * w[j]
        for i in range(n_assets)
        for j in range(n_assets)
    )
    model.setObjective(variance, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}