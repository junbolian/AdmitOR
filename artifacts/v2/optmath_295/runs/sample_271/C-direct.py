import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]
    cov_0_1 = params["cov_0_1"]
    cov_0_2 = params["cov_0_2"]
    covariance_scale = params["covariance_scale"]

    n = 6

    # Build the covariance matrix.
    # Diagonal (variance) and off-diagonal entries not explicitly named
    # are anchored at the example values scaled by covariance_scale.
    # The two explicitly parameterized entries (cov_0_1, cov_0_2) use their
    # param values directly (they already carry any scaling the caller intends).
    #
    # Example anchor values (from the problem description):
    base = [
        [0.0100, 0.0216, 0.0471, 0.0100, 0.0100, 0.0100],
        [0.0216, 0.0144, 0.0100, 0.0100, 0.0100, 0.0100],
        [0.0471, 0.0100, 0.0225, 0.0100, 0.0100, 0.0100],
        [0.0100, 0.0100, 0.0100, 0.0196, 0.0100, 0.0100],
        [0.0100, 0.0100, 0.0100, 0.0100, 0.0169, 0.0100],
        [0.0100, 0.0100, 0.0100, 0.0100, 0.0100, 0.0256],
    ]

    # Apply covariance_scale to all entries, then override the two named ones.
    cov = [[covariance_scale * base[i][j] for j in range(n)] for i in range(n)]
    cov[0][1] = cov_0_1
    cov[1][0] = cov_0_1
    cov[0][2] = cov_0_2
    cov[2][0] = cov_0_2

    model = gp.Model("portfolio")
    model.setParam("OutputFlag", 0)

    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Budget constraint: weights sum to exactly `budget`
    model.addConstr(gp.quicksum(w[i] for i in range(n)) == budget, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return,
        name="min_return"
    )

    # Objective: minimize portfolio variance = w^T * Cov * w
    variance = gp.quicksum(
        cov[i][j] * w[i] * w[j]
        for i in range(n)
        for j in range(n)
    )
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