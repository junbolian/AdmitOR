import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 5
    cov = [
        [0.0250, 0.0080, 0.0110, 0.0050, 0.0090],
        [0.0080, 0.0300, 0.0130, 0.0045, 0.0120],
        [0.0110, 0.0130, 0.0400, 0.0060, 0.0150],
        [0.0050, 0.0045, 0.0060, 0.0200, 0.0070],
        [0.0090, 0.0120, 0.0150, 0.0070, 0.0350],
    ]
    exp_ret = params["expected_returns"]
    min_ret = params["min_return"]
    max_w = params["max_weight"]
    budget = params["budget_sum_weights"]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)
    model.w = pyo.Var(model.assets, domain=pyo.NonNegativeReals)

    model.cov = pyo.Param(
        model.assets, model.assets, initialize=lambda m, i, j: cov[i][j]
    )

    def portfolio_variance_rule(m):
        return sum(m.cov[i, j] * m.w[i] * m.w[j] for i in m.assets for j in m.assets)

    model.portfolio_variance = pyo.Expression(rule=portfolio_variance_rule)
    model.variance = pyo.Objective(expr=model.portfolio_variance, sense=pyo.minimize)

    def budget_rule(m):
        return sum(m.w[i] for i in m.assets) == budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def return_rule(m):
        return sum(exp_ret[i] * m.w[i] for i in m.assets) >= min_ret

    model.return_con = pyo.Constraint(rule=return_rule)

    def cap_rule(m, i):
        return m.w[i] <= max_w

    model.cap_con = pyo.Constraint(model.assets, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.portfolio_variance))
    return {"objective": obj_val, "status": "optimal"}