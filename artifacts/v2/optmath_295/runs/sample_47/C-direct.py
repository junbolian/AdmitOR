import gurobipy as gp
from gurobipy import GRB


def solve(params):
    expected_returns = params["expected_returns"]
    n = len(expected_returns)

    variances = params["variances"]
    covariances = params["covariances"]
    min_return = params["min_return"]
    sum_allocation = params["sum_allocation"]
    max_weight = params["max_weight"]

    # Reconstruct the full covariance matrix from diagonals and ordered off-diagonals.
    cov = [[0.0] * n for _ in range(n)]
    for i in range(n):
        cov[i][i] = variances[i]

    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    for k, (i, j) in enumerate(pairs):
        cov[i][j] = covariances[k]
        cov[j][i] = covariances[k]

    model = gp.Model("portfolio")
    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    variance = (
        gp.quicksum(w[i] * w[i] * cov[i][i] for i in range(n))
        + 2 * gp.quicksum(
            w[i] * w[j] * cov[i][j]
            for i in range(n)
            for j in range(i + 1, n)
        )
    )
    model.setObjective(variance, GRB.MINIMIZE)

    model.addConstr(gp.quicksum(w[i] for i in range(n)) == sum_allocation, name="budget")
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return,
        name="min_return_constr",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}