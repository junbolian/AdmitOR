import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns_raw = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    cov_0_1 = params["covariance_0_1"]
    cov_0_2 = params["covariance_0_2"]

    n_assets = 10

    # Handle expected_returns as list or scalar
    if hasattr(expected_returns_raw, '__iter__'):
        expected_returns = list(expected_returns_raw)
    else:
        # Scalar: broadcast to all assets
        expected_returns = [float(expected_returns_raw)] * n_assets

    # Pad or trim to exactly n_assets
    if len(expected_returns) < n_assets:
        last_val = expected_returns[-1] if expected_returns else 0.0
        expected_returns = expected_returns + [last_val] * (n_assets - len(expected_returns))
    else:
        expected_returns = expected_returns[:n_assets]

    # Handle max_allocation as scalar or list
    if hasattr(max_allocation, '__iter__'):
        max_alloc_list = list(max_allocation)
        if len(max_alloc_list) < n_assets:
            last_val = max_alloc_list[-1] if max_alloc_list else 1.0
            max_alloc_list = max_alloc_list + [last_val] * (n_assets - len(max_alloc_list))
        max_alloc_list = max_alloc_list[:n_assets]
    else:
        max_alloc_list = [float(max_allocation)] * n_assets

    # Build covariance matrix:
    #   diagonal = 1.0 (unit variance per asset)
    #   C[0][1] = C[1][0] = cov_0_1
    #   C[0][2] = C[2][0] = cov_0_2
    #   all other off-diagonal = 0
    cov = [[0.0] * n_assets for _ in range(n_assets)]
    for i in range(n_assets):
        cov[i][i] = 1.0
    cov[0][1] = cov_0_1
    cov[1][0] = cov_0_1
    cov[0][2] = cov_0_2
    cov[2][0] = cov_0_2

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: allocation weights
    w = model.addVars(n_assets, lb=0.0, name="w")
    for i in range(n_assets):
        w[i].ub = max_alloc_list[i]

    # Total allocation constraint
    model.addConstr(
        gp.quicksum(w[i] for i in range(n_assets)) == total_allocation,
        name="total_alloc"
    )

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(float(expected_returns[i]) * w[i] for i in range(n_assets)) >= min_return,
        name="min_return"
    )

    # Objective: minimize portfolio variance = w^T * Cov * w
    variance = gp.QuadExpr()
    for i in range(n_assets):
        for j in range(n_assets):
            if cov[i][j] != 0.0:
                variance += cov[i][j] * w[i] * w[j]

    model.setObjective(variance, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}