import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    min_return = params["min_return"]
    covariance_0_1 = params["covariance_0_1"]
    covariance_0_2 = params["covariance_0_2"]

    n = len(expected_returns)

    variances = [0.10 + 0.01 * i for i in range(n)]
    cov = [[0.0] * n for _ in range(n)]
    for i in range(n):
        cov[i][i] = variances[i]
    cov[0][1] = covariance_0_1
    cov[1][0] = covariance_0_1
    cov[0][2] = covariance_0_2
    cov[2][0] = covariance_0_2

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)
    model.w = pyo.Var(model.assets, bounds=(0, max_allocation))

    def variance_rule(m):
        return sum(cov[i][j] * m.w[i] * m.w[j] for i in range(n) for j in range(n))

    model.portfolio_variance = pyo.Expression(rule=variance_rule)
    model.obj = pyo.Objective(expr=model.portfolio_variance, sense=pyo.minimize)

    model.total_con = pyo.Constraint(expr=sum(model.w[i] for i in model.assets) == total_allocation)
    model.return_con = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in model.assets) >= min_return
    )

    Highs().solve(model)
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "no solution"}
    return {"objective": obj_val, "status": "optimal"}