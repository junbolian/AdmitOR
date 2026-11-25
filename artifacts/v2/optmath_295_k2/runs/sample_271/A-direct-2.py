import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    max_weight = params["max_weight"]
    covariance_0_1 = params["covariance_0_1"]
    covariance_0_2 = params["covariance_0_2"]

    n = len(expected_returns)
    assets = list(range(n))

    model = pyo.ConcreteModel()

    model.assets = pyo.Set(initialize=assets)

    model.w = pyo.Var(model.assets, bounds=(0, None))

    # Build the covariance matrix.
    # Diagonal entries (variances) default to the expected returns (used as proxy
    # variances); off-diagonal entries default to zero except the two provided.
    cov = {}
    for i in assets:
        for j in assets:
            if i == j:
                cov[i, j] = float(expected_returns[i])
            else:
                cov[i, j] = 0.0
    if n > 1:
        cov[0, 1] = float(covariance_0_1)
        cov[1, 0] = float(covariance_0_1)
    if n > 2:
        cov[0, 2] = float(covariance_0_2)
        cov[2, 0] = float(covariance_0_2)

    # Full quadratic objective handled by HiGHS via a quadratic expression.
    def variance_rule(m):
        expr = 0
        for i in m.assets:
            for j in m.assets:
                if cov[i, j] != 0.0:
                    expr += m.w[i] * m.w[j] * cov[i, j]
        return expr

    model.variance = pyo.Objective(rule=variance_rule, sense=pyo.minimize)

    model.budget = pyo.Constraint(
        expr=sum(model.w[i] for i in model.assets) == 1
    )

    model.ret = pyo.Constraint(
        expr=sum(float(expected_returns[i]) * model.w[i] for i in model.assets)
        >= float(min_expected_return)
    )

    def cap_rule(m, i):
        return m.w[i] <= float(max_weight)

    model.cap = pyo.Constraint(model.assets, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.variance))
    return {"objective": obj_val, "status": "optimal"}