import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = list(params["expected_returns"])
    min_return = params["min_return"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    n_assets = len(expected_returns)
    asset_ids = list(range(n_assets))

    # Covariance proxy built from expected returns (diagonal variances,
    # symmetric off-diagonal covariances). Scaled to be positive definite.
    variances = [r * r for r in expected_returns]
    cov = {}
    for i in asset_ids:
        for j in asset_ids:
            if i == j:
                cov[(i, j)] = variances[i]
            else:
                cov[(i, j)] = 0.1 * (variances[i] * variances[j]) ** 0.5

    model = pyo.ConcreteModel()

    model.assets = pyo.Set(initialize=asset_ids)

    model.w = pyo.Var(model.assets, domain=pyo.NonNegativeReals)

    model.budget_con = pyo.Constraint(
        expr=sum(model.w[i] for i in model.assets) == budget
    )

    model.return_con = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in model.assets) >= min_return
    )

    model.max_weight_con = pyo.Constraint(
        model.assets, rule=lambda mm, i: mm.w[i] <= max_weight
    )

    # Quadratic objective expressed directly (no pyo.Expression wrapper)
    model.obj = pyo.Objective(
        expr=sum(
            cov[(i, j)] * model.w[i] * model.w[j]
            for i in model.assets
            for j in model.assets
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}