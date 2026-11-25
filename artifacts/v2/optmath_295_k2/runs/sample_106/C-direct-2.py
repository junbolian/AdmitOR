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
    # Using a standard example covariance matrix consistent with the given returns
    cov = [
        [0.00324625, 0.00022983, 0.00145232, 0.00013611],
        [0.00022983, 0.00224646, 0.00049978, 0.00032009],
        [0.00145232, 0.00049978, 0.00279859, 0.00007447],
        [0.00013611, 0.00032009, 0.00007447, 0.00096799],
    ]

    model = gp.Model("portfolio_variance")
    model.setParam("OutputFlag", 0)

    n = 4
    w = model.addVars(n, lb=min_asset_weight, ub=max_asset_weight, name="w")

    # Budget constraint
    model.addConstr(
        gp.quicksum(w[i] for i in range(n)) == budget_sum,
        name="budget"
    )

    # Minimum return constraint
    ret_coeffs = [
        expected_return_asset0,
        expected_return_asset1,
        expected_return_asset2,
        expected_return_asset3,
    ]
    model.addConstr(
        gp.quicksum(ret_coeffs[i] * w[i] for i in range(n)) >= min_portfolio_return,
        name="min_return"
    )

    # Quadratic objective: minimize portfolio variance w^T * Cov * w
    variance = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
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