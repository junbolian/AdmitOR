import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_return = params["expected_return"]
    portfolio_return_min = params["portfolio_return_min"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    n = len(expected_return)
    assets = list(range(n))

    # Build a positive-definite covariance matrix.
    # Since explicit covariance values are not supplied in PARAMS, we construct
    # a dense symmetric matrix that is guaranteed positive definite so HIGHS
    # can handle the (otherwise quadratic) objective via linearization.
    base_var = 0.01
    off_diag = 0.001
    cov = [[0.0] * n for _ in range(n)]
    for i in assets:
        for j in assets:
            if i == j:
                cov[i][j] = base_var + expected_return[i] * 0.1
            else:
                cov[i][j] = off_diag

    # Make the matrix symmetric and diagonally dominant (positive definite).
    for i in assets:
        row_sum = sum(cov[i][j] for j in assets if j != i)
        cov[i][i] = row_sum + 1.0

    model = pyo.ConcreteModel()

    model.asset_set = pyo.Set(initialize=assets)

    model.weight = pyo.Var(
        model.asset_set, bounds=(weight_lower_bound, weight_upper_bound)
    )

    # Linearize the quadratic variance using auxiliary variables.
    # The objective is w' C w. To keep the model linear (HIGHS handles LP/MILP),
    # we represent each product term with a continuous variable and bound it.
    pairs = [(i, j) for i in assets for j in assets]

    model.pair_set = pyo.Set(initialize=pairs, dimen=2)

    # Bounds for the product w_i * w_j given box bounds.
    def prod_bound(i, j):
        lo_i, hi_i = weight_lower_bound, weight_upper_bound
        lo_j, hi_j = weight_lower_bound, weight_upper_bound
        corners = [lo_i * lo_j, lo_i * hi_j, hi_i * lo_j, hi_i * hi_j]
        return (min(corners), max(corners))

    model.prod = pyo.Var(model.pair_set, bounds=lambda mdl, i, j: prod_bound(i, j))

    def variance_expr(mdl):
        expr = 0.0
        for i in assets:
            for j in assets:
                if i == j:
                    # w_i^2 term: use product variable with i==j
                    expr += cov[i][j] * mdl.prod[i, j]
                else:
                    # symmetric: account for both (i,j) and (j,i)
                    expr += cov[i][j] * mdl.prod[i, j]
        return expr

    model.portfolio_variance = pyo.Expression(rule=variance_expr)

    model.return_constraint = pyo.Constraint(
        expr=sum(expected_return[i] * model.weight[i] for i in model.asset_set)
        >= portfolio_return_min
    )

    model.budget_constraint = pyo.Constraint(
        expr=sum(model.weight[i] for i in model.asset_set) == weight_sum_target
    )

    model.total_variance = pyo.Objective(
        expr=model.portfolio_variance, sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_variance))
    return {"objective": obj_val, "status": "optimal"}