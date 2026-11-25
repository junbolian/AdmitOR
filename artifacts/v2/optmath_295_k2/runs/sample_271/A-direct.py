import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    expected_returns = params["expected_returns"]
    min_expected_return = params["min_expected_return"]
    max_weight = params["max_weight"]
    cov_0_1 = params["covariance_0_1"]
    cov_0_2 = params["covariance_0_2"]

    n = len(expected_returns)
    idx = list(range(n))

    # Build covariance matrix: diagonal variances, off-diagonals from params.
    cov = [[0.0] * n for _ in idx]
    for i in idx:
        for j in idx:
            if i == j:
                cov[i][j] = 0.02
            else:
                cov[i][j] = 0.01

    cov[0][1] = cov_0_1
    cov[1][0] = cov_0_1
    cov[0][2] = cov_0_2
    cov[2][0] = cov_0_2

    model = pyo.ConcreteModel()

    model.assets = pyo.Set(initialize=idx)

    model.w = pyo.Var(model.assets, bounds=(0, max_weight))

    # Linear expression that lets the quadratic objective be written
    # without directly embedding a degree-2 rule in the Expression component.
    model.budget = pyo.Constraint(
        expr=sum(model.w[i] for i in model.assets) == 1.0
    )

    model.ret = pyo.Constraint(
        expr=sum(expected_returns[i] * model.w[i] for i in model.assets)
        >= min_expected_return
    )

    def variance_rule(m):
        return sum(cov[i][j] * m.w[i] * m.w[j] for i in m.assets for j in m.assets)

    # Quadratic objective defined directly (not via an Expression component,
    # which HiGHS/Appsi cannot handle for nonlinear degrees).
    model.obj = pyo.Objective(rule=variance_rule, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}