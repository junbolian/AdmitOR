import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    er = params["expected_returns"]
    min_return = params["min_return"]
    sum_allocation = params["sum_allocation"]
    max_weight = params["max_weight"]
    variances = params["variances"]
    covariances = params["covariances"]

    assets = list(range(4))

    def cov_value(i, j):
        if i == j:
            return variances[i]
        key = (min(i, j), max(i, j))
        if isinstance(covariances, dict):
            return covariances[key]
        # covariances given as a flat list in upper-triangular order
        pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        idx = pairs.index(key)
        return covariances[idx]

    model = pyo.ConcreteModel()

    model.w = pyo.Var(assets, bounds=(0, max_weight))

    def obj_rule(mdl):
        return sum(
            cov_value(i, j) * mdl.w[i] * mdl.w[j]
            for i in assets
            for j in assets
        )

    model.risk = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.ret_con = pyo.Constraint(
        expr=sum(er[i] * model.w[i] for i in assets) >= min_return
    )

    model.sum_con = pyo.Constraint(
        expr=sum(model.w[i] for i in assets) == sum_allocation
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.risk))
    return {"objective": obj_val, "status": "optimal"}