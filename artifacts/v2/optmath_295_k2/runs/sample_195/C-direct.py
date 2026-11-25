import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    variances = params["variances"]
    covariances = params["covariances"]
    max_weight = params["max_weight"]
    budget_sum = params["budget_sum"]

    n = 4
    cov_pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Budget constraint
    model.addConstr(gp.quicksum(w[i] for i in range(n)) == budget_sum, name="budget")

    # Minimum expected return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_expected_return,
        name="min_return"
    )

    # Quadratic objective: portfolio variance
    obj = gp.QuadExpr()
    for i in range(n):
        obj += variances[i] * w[i] * w[i]
    for idx, (i, j) in enumerate(cov_pairs):
        obj += 2.0 * covariances[idx] * w[i] * w[j]

    model.setObjective(obj, GRB.MINIMIZE)

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