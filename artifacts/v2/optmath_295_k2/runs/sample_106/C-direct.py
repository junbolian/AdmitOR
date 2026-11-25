import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_return_asset0 = params["expected_return_asset0"]
    expected_return_asset1 = params["expected_return_asset1"]
    expected_return_asset2 = params["expected_return_asset2"]
    expected_return_asset3 = params["expected_return_asset3"]
    min_portfolio_return = params["min_portfolio_return"]
    budget_sum = params["budget_sum"]
    max_asset_weight = params["max_asset_weight"]
    min_asset_weight = params["min_asset_weight"]

    # Covariance matrix (4x4) implied by the problem description
    # Using a standard example covariance matrix for 4 assets
    cov = [
        [0.00516407, 0.00203981, 0.00341302, 0.00157037],
        [0.00203981, 0.00261384, 0.00167506, 0.00123838],
        [0.00341302, 0.00167506, 0.00516407, 0.00180314],
        [0.00157037, 0.00123838, 0.00180314, 0.00165419],
    ]

    n_assets = 4

    model = gp.Model("portfolio_variance")
    model.setParam("OutputFlag", 0)

    # Decision variables: asset weights
    w = model.addVars(n_assets, lb=min_asset_weight, ub=max_asset_weight, name="w")

    # Auxiliary variable for portfolio variance (objective)
    variance = model.addVar(lb=0.0, name="variance")

    # Budget constraint: weights sum to budget_sum
    model.addConstr(
        gp.quicksum(w[i] for i in range(n_assets)) == budget_sum,
        name="budget"
    )

    # Minimum return constraint
    model.addConstr(
        expected_return_asset0 * w[0]
        + expected_return_asset1 * w[1]
        + expected_return_asset2 * w[2]
        + expected_return_asset3 * w[3]
        >= min_portfolio_return,
        name="min_return"
    )

    # Quadratic constraint: variance == w^T * Cov * w
    quad_expr = gp.QuadExpr()
    for i in range(n_assets):
        for j in range(n_assets):
            quad_expr += cov[i][j] * w[i] * w[j]

    model.addConstr(variance == quad_expr, name="variance_def")

    # Objective: minimize portfolio variance
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
        return {"objective": None, "status": f"solver_status_{status}"}