import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    returns = params["expected_returns"]
    variances = params["variances"]
    covs = params["covariances"]
    min_return = params["min_return"]
    budget_fraction = params["budget_fraction"]
    max_asset_weight = params["max_asset_weight"]

    n = len(returns)

    cov_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    cov_dict = {pair: covs[i] for i, pair in enumerate(cov_pairs)}

    def cov(i, j):
        if i == j:
            return variances[i]
        if (i, j) in cov_dict:
            return cov_dict[(i, j)]
        return cov_dict[(j, i)]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(0, max_asset_weight))

    def variance_rule(m):
        expr = 0.0
        for i in list(m.assets):
            for j in list(m.assets):
                expr += m.w[i] * m.w[j] * cov(i, j)
        return expr

    model.obj_expr = pyo.Expression(rule=variance_rule)

    # Quadratic objective must be expressed directly (HiGHS cannot take
    # a named Expression as objective; it needs the actual quadratic form).
    def objective_rule(m):
        return variance_rule(m)

    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def return_rule(m):
        return sum(m.w[i] * returns[i] for i in list(m.assets)) >= min_return

    model.return_con = pyo.Constraint(rule=return_rule)

    def budget_rule(m):
        return sum(m.w[i] for i in list(m.assets)) == budget_fraction

    model.budget_con = pyo.Constraint(rule=budget_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}