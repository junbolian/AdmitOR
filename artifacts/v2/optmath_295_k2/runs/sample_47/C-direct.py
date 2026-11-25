import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    variances = params["variances"]
    covariances = params["covariances"]
    min_return = params["min_return"]
    budget_fraction = params["budget_fraction"]
    max_asset_weight = params["max_asset_weight"]

    n_assets = 4
    assets = range(n_assets)

    # Pairwise covariance index mapping: (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
    cov_pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]

    model = gp.Model("portfolio")
    model.setParam("OutputFlag", 0)

    w = model.addVars(n_assets, lb=0.0, ub=max_asset_weight, name="w")

    # Portfolio variance (quadratic objective)
    variance_expr = gp.QuadExpr()
    for i in assets:
        variance_expr += variances[i] * w[i] * w[i]
    for idx, (i, j) in enumerate(cov_pairs):
        variance_expr += 2.0 * covariances[idx] * w[i] * w[j]

    model.setObjective(variance_expr, GRB.MINIMIZE)

    # Budget constraint: weights sum to budget_fraction
    model.addConstr(gp.quicksum(w[i] for i in assets) == budget_fraction, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in assets) >= min_return * budget_fraction,
        name="min_return"
    )

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