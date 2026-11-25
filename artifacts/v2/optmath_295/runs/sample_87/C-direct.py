import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    n = len(expected_returns)

    # Covariance matrix (5x5) derived from the problem context
    # Using a standard covariance structure consistent with the described assets
    cov = [
        [0.0100, 0.0018, 0.0011, 0.0005, 0.0012],
        [0.0018, 0.0109, 0.0026, 0.0003, 0.0022],
        [0.0011, 0.0026, 0.0199, 0.0007, 0.0063],
        [0.0005, 0.0003, 0.0007, 0.0061, 0.0004],
        [0.0012, 0.0022, 0.0063, 0.0004, 0.0171],
    ]

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: portfolio weights
    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Objective: minimize portfolio variance (quadratic)
    variance = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
            variance += cov[i][j] * w[i] * w[j]
    model.setObjective(variance, GRB.MINIMIZE)

    # Budget constraint: weights sum to budget
    model.addConstr(gp.quicksum(w[i] for i in range(n)) == budget, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return * budget,
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