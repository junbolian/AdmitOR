import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["asset_count"])
    target_return = params["target_return"]
    max_allocation = params["max_allocation"]
    total_allocation = params["total_allocation"]
    expected_returns = params["expected_returns"]
    covariance_matrix = params["covariance_matrix"]

    model = pyo.ConcreteModel()

    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(0, max_allocation))

    def return_rule(m):
        return sum(expected_returns[i] * m.w[i] for i in m.assets) >= target_return

    model.return_con = pyo.Constraint(rule=return_rule)

    def budget_rule(m):
        return sum(m.w[i] for i in m.assets) == total_allocation

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def obj_rule(m):
        return sum(
            covariance_matrix[i][j] * m.w[i] * m.w[j]
            for i in m.assets
            for j in m.assets
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}