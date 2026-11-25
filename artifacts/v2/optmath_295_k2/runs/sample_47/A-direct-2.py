import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    variances = params["variances"]
    covariances = params["covariances"]
    min_return = params["min_return"]
    budget_fraction = params["budget_fraction"]
    max_asset_weight = params["max_asset_weight"]

    n = len(expected_returns)
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    def cov(i, j):
        if i == j:
            return variances[i]
        lo, hi = (i, j) if i < j else (j, i)
        return covariances[pairs.index((lo, hi))]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)
    model.x = pyo.Var(model.assets, bounds=(0.0, max_asset_weight))

    def variance_rule(m):
        expr = 0
        for i in m.assets:
            for j in m.assets:
                expr += cov(i, j) * m.x[i] * m.x[j]
        return expr

    model.portfolio_variance = pyo.Expression(rule=variance_rule)

    def obj_rule(m):
        return m.portfolio_variance

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def return_rule(m):
        return sum(expected_returns[i] * m.x[i] for i in m.assets) >= min_return

    model.return_constraint = pyo.Constraint(rule=return_rule)

    def budget_rule(m):
        return sum(m.x[i] for i in m.assets) == budget_fraction

    model.budget_constraint = pyo.Constraint(rule=budget_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.portfolio_variance))
    return {"objective": obj_val, "status": "optimal"}