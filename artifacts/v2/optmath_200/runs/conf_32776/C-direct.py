import gurobipy as gp
from gurobipy import GRB

def solve(params):
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]

    # Eight assets with fixed expected returns and covariance matrix
    n = 8
    expected_returns = [0.10, 0.12, 0.08, 0.15, 0.09, 0.11, 0.13, 0.07]

    # Covariance matrix (8x8, symmetric positive semi-definite)
    cov = [
        [0.0100, 0.0018, 0.0011, 0.0021, 0.0015, 0.0013, 0.0019, 0.0010],
        [0.0018, 0.0144, 0.0020, 0.0025, 0.0014, 0.0016, 0.0022, 0.0012],
        [0.0011, 0.0020, 0.0081, 0.0014, 0.0011, 0.0010, 0.0013, 0.0009],
        [0.0021, 0.0025, 0.0014, 0.0225, 0.0018, 0.0020, 0.0024, 0.0013],
        [0.0015, 0.0014, 0.0011, 0.0018, 0.0064, 0.0012, 0.0015, 0.0008],
        [0.0013, 0.0016, 0.0010, 0.0020, 0.0012, 0.0121, 0.0017, 0.0009],
        [0.0019, 0.0022, 0.0013, 0.0024, 0.0015, 0.0017, 0.0169, 0.0011],
        [0.0010, 0.0012, 0.0009, 0.0013, 0.0008, 0.0009, 0.0011, 0.0049],
    ]

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: weights for each asset
    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Budget constraint: sum of weights equals budget
    model.addConstr(gp.quicksum(w[i] for i in range(n)) == budget, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return * budget,
        name="min_return"
    )

    # Objective: minimize portfolio variance (quadratic)
    portfolio_variance = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
            portfolio_variance += cov[i][j] * w[i] * w[j]

    model.setObjective(portfolio_variance, GRB.MINIMIZE)

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