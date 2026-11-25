import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    variances = params["variances"]
    covariances = params["covariances"]
    min_return = params["min_return"]
    budget_fraction = params["budget_fraction"]
    max_asset_weight = params["max_asset_weight"]

    n = 4
    assets = range(n)

    # Pairwise covariance index order: (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
    cov_pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    cov_map = {pair: covariances[k] for k, pair in enumerate(cov_pairs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    w = model.addVars(n, lb=0.0, ub=max_asset_weight, name="w")

    # Minimize portfolio variance: sum_i var_i * w_i^2 + 2 * sum_{i<j} cov_ij * w_i * w_j
    obj = gp.QuadExpr()
    for i in assets:
        obj += variances[i] * w[i] * w[i]
    for (i, j), cov_val in cov_map.items():
        obj += 2.0 * cov_val * w[i] * w[j]

    model.setObjective(obj, GRB.MINIMIZE)

    # Budget constraint
    model.addConstr(gp.quicksum(w[i] for i in assets) == budget_fraction, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in assets) >= min_return,
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
        return {"objective": None, "status": f"status_{status}"}