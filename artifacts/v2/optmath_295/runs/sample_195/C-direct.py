import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = [
        params["expected_return_0"],
        params["expected_return_1"],
        params["expected_return_2"],
        params["expected_return_3"],
    ]
    variances = [
        params["variance_0"],
        params["variance_1"],
        params["variance_2"],
        params["variance_3"],
    ]
    cov = {
        (0, 1): params["covariance_01"],
        (0, 2): params["covariance_02"],
        (0, 3): params["covariance_03"],
        (1, 2): params["covariance_12"],
        (1, 3): params["covariance_13"],
        (2, 3): params["covariance_23"],
    }
    min_return = params["min_return"]
    sum_weights = params["sum_weights"]
    max_weight = params["max_weight"]

    n = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Objective: minimize portfolio variance
    portfolio_variance = gp.QuadExpr()
    for i in range(n):
        portfolio_variance += variances[i] * w[i] * w[i]
    for (i, j), c in cov.items():
        portfolio_variance += 2.0 * c * w[i] * w[j]

    model.setObjective(portfolio_variance, GRB.MINIMIZE)

    # Constraint: minimum expected return
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return,
        name="min_return"
    )

    # Constraint: weights sum to sum_weights
    model.addConstr(
        gp.quicksum(w[i] for i in range(n)) == sum_weights,
        name="sum_weights"
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