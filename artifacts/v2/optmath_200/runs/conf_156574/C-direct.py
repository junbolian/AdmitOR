import gurobipy as gp
from gurobipy import GRB
import numpy as np

def solve(params):
    expected_return = params["expected_return"]
    portfolio_return_min = params["portfolio_return_min"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    n_assets = 10

    # Generate a positive semi-definite covariance matrix from the expected returns
    # Use a correlation structure consistent with the problem description
    np.random.seed(42)
    # Build a covariance matrix: use volatilities proportional to expected returns
    # and a base correlation structure
    volatilities = np.array([er * 1.5 + 0.05 for er in expected_return])
    
    # Create a random correlation matrix
    rng = np.random.default_rng(42)
    A = rng.standard_normal((n_assets, n_assets))
    corr = A @ A.T
    # Normalize to get correlation matrix
    d = np.sqrt(np.diag(corr))
    corr = corr / np.outer(d, d)
    
    # Scale by volatilities to get covariance matrix
    cov_matrix = np.outer(volatilities, volatilities) * corr

    # Ensure PSD by adding small diagonal perturbation if needed
    min_eig = np.min(np.linalg.eigvalsh(cov_matrix))
    if min_eig < 0:
        cov_matrix += (-min_eig + 1e-8) * np.eye(n_assets)

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: weights
    weights = model.addVars(n_assets, lb=weight_lower_bound, ub=weight_upper_bound,
                             name="weights")

    # Objective: minimize portfolio variance (quadratic)
    portfolio_variance = gp.QuadExpr()
    for i in range(n_assets):
        for j in range(n_assets):
            portfolio_variance += cov_matrix[i, j] * weights[i] * weights[j]

    model.setObjective(portfolio_variance, GRB.MINIMIZE)

    # Constraint: weights sum to target (fully invested)
    model.addConstr(
        gp.quicksum(weights[i] for i in range(n_assets)) == weight_sum_target,
        name="full_investment"
    )

    # Constraint: minimum required return
    model.addConstr(
        gp.quicksum(expected_return[i] * weights[i] for i in range(n_assets)) >= portfolio_return_min,
        name="min_return"
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