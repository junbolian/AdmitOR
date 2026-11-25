import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]
    cov_0_1 = params["cov_0_1"]
    cov_0_2 = params["cov_0_2"]
    covariance_scale = params["covariance_scale"]

    n = 6
    assets = list(range(n))

    # Base covariance coefficients for all off-diagonal pairs; anchored so the
    # two given values hold exactly and the rest scale multiplicatively.
    base_cov = {
        (0, 1): cov_0_1,
        (0, 2): cov_0_2,
        (1, 2): 0.0430,
        (0, 3): 0.0311,
        (1, 3): 0.0343,
        (2, 3): 0.0375,
        (0, 4): 0.0259,
        (1, 4): 0.0298,
        (2, 4): 0.0331,
        (3, 4): 0.0402,
        (0, 5): 0.0233,
        (1, 5): 0.0267,
        (2, 5): 0.0299,
        (3, 5): 0.0354,
        (4, 5): 0.0388,
    }
    diag_cov = {0: 0.0421, 1: 0.0387, 2: 0.0332, 3: 0.0365, 4: 0.0318, 5: 0.0449}

    def cov(i, j):
        if i == j:
            return diag_cov[i]
        key = (min(i, j), max(i, j))
        return base_cov[key] * covariance_scale

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=assets, ordered=True)

    model.w = pyo.Var(model.assets, bounds=(0.0, max_weight))

    # Quadratic objective built with a helper Pyomo Expression so that the
    # degrees of the objective are tracked correctly by the HiGHS interface.
    model.portfolio_variance = pyo.Expression(
        expr=sum(
            model.w[i] * model.w[j] * cov(i, j)
            for i in model.assets
            for j in model.assets
        )
    )
    model.obj = pyo.Objective(expr=model.portfolio_variance, sense=pyo.minimize)

    def budget_rule(m):
        return sum(m.w[i] for i in m.assets) == budget

    model.budget_constraint = pyo.Constraint(rule=budget_rule)

    def return_rule(m):
        return sum(expected_returns[i] * m.w[i] for i in m.assets) >= min_return

    model.return_constraint = pyo.Constraint(rule=return_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}