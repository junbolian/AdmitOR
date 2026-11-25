import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    cov_0_1 = params["covariance_0_1"]
    cov_0_2 = params["covariance_0_2"]

    n = 10

    # Ensure expected_returns is indexable as a list
    if not hasattr(expected_returns, '__len__'):
        expected_returns = list(expected_returns)
    else:
        expected_returns = list(expected_returns)

    # Diagonal variances are structural constants (not provided in params)
    variances = [0.1, 0.08, 0.12, 0.09, 0.11, 0.07, 0.13, 0.095, 0.085, 0.10]

    cov = [[0.0] * n for _ in range(n)]
    for i in range(n):
        cov[i][i] = variances[i]

    # Parameterized cross-covariances
    cov[0][1] = cov_0_1
    cov[1][0] = cov_0_1
    cov[0][2] = cov_0_2
    cov[2][0] = cov_0_2

    model = gp.Model("min_variance_portfolio")
    model.setParam("OutputFlag", 0)

    # Decision variables: weight for each asset
    w = model.addVars(n, lb=0.0, ub=max_allocation, name="w")

    # Total allocation constraint
    model.addConstr(
        gp.quicksum(w[i] for i in range(n)) == total_allocation,
        name="total_alloc"
    )

    # Minimum return constraint
    # If total_allocation is 1.0 (100%), weighted return >= min_return * total_allocation
    model.addConstr(
        gp.quicksum(float(expected_returns[i]) * w[i] for i in range(n)) >= float(min_return) * float(total_allocation),
        name="min_ret"
    )

    # Portfolio variance as quadratic objective
    variance = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
            if cov[i][j] != 0.0:
                variance += cov[i][j] * w[i] * w[j]

    model.setObjective(variance, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}