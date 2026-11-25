import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    max_weight = params["max_weight"]
    cov_0_1 = params["covariance_0_1"]
    cov_0_2 = params["covariance_0_2"]

    n_assets = 6

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: weights for each asset
    w = model.addVars(n_assets, lb=0.0, ub=max_weight, name="w")

    # Constraint: weights sum to 1
    model.addConstr(gp.quicksum(w[i] for i in range(n_assets)) == 1.0, name="budget")

    # Constraint: minimum expected return
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n_assets)) >= min_expected_return,
        name="min_return"
    )

    # Portfolio variance objective
    # We only have covariance for (0,1) and (0,2) explicitly parameterized.
    # All other covariance terms are assumed zero (diagonal entries also zero unless specified).
    # Build quadratic objective: sum over all pairs
    # For pairs with known covariance use the params; others default to zero variance contribution
    # (The problem only provides two off-diagonal covariances; diagonal variances not given -> treat as 0)
    portfolio_variance = (
        2.0 * cov_0_1 * w[0] * w[1] +
        2.0 * cov_0_2 * w[0] * w[2]
    )

    model.setObjective(portfolio_variance, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}