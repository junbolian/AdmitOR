import gurobipy as gp
from gurobipy import GRB

def solve(params):
    returns = params["returns"]
    min_return = params["min_return"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    n_assets = 4

    # Covariance matrix implied by the problem description (standard Markowitz)
    # Since no covariance matrix is provided in params, we build a minimal positive-definite
    # identity-scaled Q so the problem is well-posed. The problem states "portfolio variance
    # is defined by a quadratic constraint involving the asset weights"; without an explicit
    # covariance matrix in PARAMS, we use the identity matrix (each asset has unit variance,
    # zero covariance), which is the standard assumption when no covariance data is supplied.
    # This gives variance = sum(w_i^2).
    Q = [[1.0 if i == j else 0.0 for j in range(n_assets)] for i in range(n_assets)]

    model = gp.Model("portfolio")
    model.setParam("OutputFlag", 0)

    # Decision variables: asset weights
    w = model.addVars(n_assets, lb=weight_lower_bound, ub=weight_upper_bound, name="w")

    # Objective: minimize portfolio variance = w^T Q w
    obj = gp.QuadExpr()
    for i in range(n_assets):
        for j in range(n_assets):
            if Q[i][j] != 0.0:
                obj += Q[i][j] * w[i] * w[j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint: weights sum to budget target
    model.addConstr(gp.quicksum(w[i] for i in range(n_assets)) == weight_sum_target, name="budget")

    # Constraint: minimum return
    model.addConstr(
        gp.quicksum(returns[i] * w[i] for i in range(n_assets)) >= min_return,
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