import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    variances = params["variances"]
    covariances = params["covariances"]
    max_weight = params["max_weight"]
    budget_sum = params["budget_sum"]

    n = len(expected_returns)
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    # Symmetric covariance matrix
    cov_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        cov_matrix[i][i] = variances[i]
    for k, (i, j) in enumerate(pairs):
        cov_matrix[i][j] = covariances[k]
        cov_matrix[j][i] = covariances[k]

    model = pyo.ConcreteModel()
    model.assets = pyo.RangeSet(0, n - 1)
    model.w = pyo.Var(model.assets, bounds=(0, max_weight))

    # Full quadratic objective (no factor of 1/2 needed since it's just scaling)
    model.obj = pyo.Objective(
        expr=sum(
            cov_matrix[i][j] * model.w[i] * model.w[j]
            for i in range(n)
            for j in range(n)
        ),
        sense=pyo.minimize,
    )

    model.return_constraint = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in range(n))
        >= min_expected_return
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(model.w[i] for i in range(n)) == budget_sum
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}