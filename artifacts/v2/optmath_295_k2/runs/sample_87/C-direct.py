import gurobipy as gp
from gurobipy import GRB


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget_sum_weights = params["budget_sum_weights"]

    n_assets = len(expected_returns)

    # Attempt to load covariance matrix from any recognized key in params.
    cov_matrix = None
    for key in ("cov_matrix", "covariance_matrix", "covariances", "cov", "Sigma", "sigma"):
        if key in params:
            cov_matrix = params[key]
            break

    # If no covariance matrix is provided, construct one from expected returns.
    # Use a factor model: Cov[i,j] = r[i]*r[j] (rank-1 market factor) plus
    # a diagonal idiosyncratic term to ensure positive definiteness.
    if cov_matrix is None:
        r = expected_returns
        idio_scale = 0.01  # 1% idiosyncratic variance per asset
        cov_matrix = [
            [r[i] * r[j] + (idio_scale if i == j else 0.0) for j in range(n_assets)]
            for i in range(n_assets)
        ]

    model = gp.Model("portfolio")
    model.Params.OutputFlag = 0

    w = model.addVars(n_assets, lb=0.0, ub=max_weight, name="w")

    # Minimize portfolio variance: w^T * Cov * w
    variance = gp.QuadExpr()
    for i in range(n_assets):
        for j in range(n_assets):
            variance += cov_matrix[i][j] * w[i] * w[j]
    model.setObjective(variance, GRB.MINIMIZE)

    # Budget: total allocation must equal budget_sum_weights
    model.addConstr(
        gp.quicksum(w[i] for i in range(n_assets)) == budget_sum_weights,
        name="budget",
    )

    # Minimum expected return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n_assets)) >= min_return,
        name="min_return",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}