import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    expected_returns = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    cov_0_1 = params["covariance_0_1"]
    cov_0_2 = params["covariance_0_2"]

    n = 10

    cov = [[0.0] * n for _ in range(n)]
    cov[0][1] = cov_0_1
    cov[1][0] = cov_0_1
    cov[0][2] = cov_0_2
    cov[2][0] = cov_0_2

    diag = [0.0] * n
    for i in range(n):
        if i == 0:
            diag[i] = abs(cov_0_1) + abs(cov_0_2) + 0.1
        elif i == 1:
            diag[i] = abs(cov_0_1) + 0.1
        elif i == 2:
            diag[i] = abs(cov_0_2) + 0.1
        else:
            diag[i] = 0.15
        cov[i][i] = diag[i]

    for i in range(n):
        for j in range(i + 1, n):
            if cov[i][j] == 0.0 and not (i == 0 and j == 1) and not (i == 0 and j == 2):
                cov[i][j] = 0.01
                cov[j][i] = 0.01

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)

    model.weights = pyo.Var(model.assets, bounds=(0.0, max_allocation))

    def variance_rule(mdl):
        expr = 0.0
        for i in mdl.assets:
            for j in mdl.assets:
                expr += cov[i][j] * mdl.weights[i] * mdl.weights[j]
        return expr

    model.variance = pyo.Expression(rule=variance_rule)

    model.budget = pyo.Constraint(
        expr=sum(model.weights[i] for i in model.assets) == total_allocation
    )

    model.min_return_con = pyo.Constraint(
        expr=sum(expected_returns[i] * model.weights[i] for i in model.assets)
        >= min_return * total_allocation
    )

    model.obj = pyo.Objective(expr=model.variance, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}