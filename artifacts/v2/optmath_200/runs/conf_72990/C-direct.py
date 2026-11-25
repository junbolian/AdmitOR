import gurobipy as gp
from gurobipy import GRB

def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    n = len(expected_returns)

    # Covariance matrix (fixed structural data for 8 assets)
    cov = [
        [0.00357, 0.00057, 0.00010, 0.00034, 0.00023, 0.00042, 0.00018, 0.00020],
        [0.00057, 0.00289, 0.00015, 0.00028, 0.00019, 0.00055, 0.00012, 0.00014],
        [0.00010, 0.00015, 0.00198, 0.00022, 0.00016, 0.00018, 0.00025, 0.00022],
        [0.00034, 0.00028, 0.00022, 0.00245, 0.00031, 0.00033, 0.00020, 0.00018],
        [0.00023, 0.00019, 0.00016, 0.00031, 0.00213, 0.00027, 0.00015, 0.00016],
        [0.00042, 0.00055, 0.00018, 0.00033, 0.00027, 0.00274, 0.00014, 0.00016],
        [0.00018, 0.00012, 0.00025, 0.00020, 0.00015, 0.00014, 0.00187, 0.00019],
        [0.00020, 0.00014, 0.00022, 0.00018, 0.00016, 0.00016, 0.00019, 0.00195],
    ]

    model = gp.Model("portfolio_optimization")
    model.setParam("OutputFlag", 0)

    w = model.addVars(n, lb=0.0, ub=max_weight, name="w")

    # Objective: minimize portfolio variance
    obj = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
            obj += cov[i][j] * w[i] * w[j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Budget constraint
    model.addConstr(gp.quicksum(w[i] for i in range(n)) == budget, name="budget")

    # Minimum return constraint
    model.addConstr(
        gp.quicksum(expected_returns[i] * w[i] for i in range(n)) >= min_return,
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