import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    n = len(expected_returns)
    assets = list(range(n))

    cov = [
        [0.0165, 0.0032, 0.0050, 0.0012, 0.0030],
        [0.0032, 0.0172, 0.0041, 0.0020, 0.0055],
        [0.0050, 0.0041, 0.0245, 0.0011, 0.0062],
        [0.0012, 0.0020, 0.0011, 0.0089, 0.0009],
        [0.0030, 0.0055, 0.0062, 0.0009, 0.0211],
    ]

    model = pyo.ConcreteModel()

    model.w = pyo.Var(assets, bounds=(0.0, max_weight))

    model.budget_con = pyo.Constraint(
        expr=sum(model.w[i] for i in assets) == budget
    )

    model.return_con = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in assets) >= min_return
    )

    # Build quadratic objective explicitly from the flattened covariance
    model.obj = pyo.Objective(sense=pyo.minimize)
    terms = []
    for i in assets:
        for j in assets:
            c = cov[i][j]
            if c != 0.0:
                terms.append(c * model.w[i] * model.w[j])
    model.obj.expr = sum(terms)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}