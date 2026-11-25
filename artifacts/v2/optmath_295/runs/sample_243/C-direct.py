import gurobipy as gp
from gurobipy import GRB


def solve(params):
    target_return = params["target_return"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    expected_returns = params["expected_returns"]
    covariance_matrix = params["covariance_matrix"]
    asset_count = params["asset_count"]

    model = gp.Model("portfolio")
    model.Params.OutputFlag = 0

    # Decision variables: portfolio weights, long-only with per-asset cap.
    w = model.addVars(
        asset_count,
        lb=0.0,
        ub=max_allocation,
        name="w",
    )

    # Full allocation constraint: weights must sum to total_allocation.
    model.addConstr(
        gp.quicksum(w[i] for i in range(asset_count)) == total_allocation,
        name="total_allocation",
    )

    # Minimum expected return constraint: weighted average return >= target_return.
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(asset_count))
        >= target_return,
        name="target_return",
    )

    # Objective: minimize portfolio variance w^T Sigma w.
    variance = gp.quicksum(
        covariance_matrix[i][j] * w[i] * w[j]
        for i in range(asset_count)
        for j in range(asset_count)
    )
    model.setObjective(variance, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"status_{model.status}"}