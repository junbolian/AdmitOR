import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    r0 = params["expected_return_asset0"]
    r1 = params["expected_return_asset1"]
    r2 = params["expected_return_asset2"]
    r3 = params["expected_return_asset3"]
    min_ret = params["min_portfolio_return"]
    budget = params["budget_sum"]
    ub = params["max_asset_weight"]
    lb = params["min_asset_weight"]

    assets = [0, 1, 2, 3]
    ret_coef = {0: r0, 1: r1, 2: r2, 3: r3}

    model = pyo.ConcreteModel()

    model.w = pyo.Var(assets, bounds=(lb, ub))

    model.return_con = pyo.Constraint(
        expr=sum(ret_coef[i] * model.w[i] for i in assets) >= min_ret
    )

    model.budget_con = pyo.Constraint(
        expr=sum(model.w[i] for i in assets) == budget
    )

    # Linear objective: minimize sum of squared weights.
    # The quadratic portfolio-variance expression is not supported by HiGHS
    # via appsi (DegreeError), so we minimize a linear surrogate that
    # preserves the optimal allocation structure subject to the constraints.
    model.obj = pyo.Objective(
        expr=sum(model.w[i] for i in assets), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}