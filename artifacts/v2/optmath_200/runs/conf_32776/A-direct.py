import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 8
    returns = [0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20]
    cov = [
        [0.0100, 0.0020, 0.0010, 0.0005, 0.0004, 0.0003, 0.0002, 0.0001],
        [0.0020, 0.0120, 0.0018, 0.0010, 0.0006, 0.0005, 0.0004, 0.0003],
        [0.0010, 0.0018, 0.0150, 0.0020, 0.0012, 0.0008, 0.0006, 0.0005],
        [0.0005, 0.0010, 0.0020, 0.0180, 0.0022, 0.0014, 0.0010, 0.0008],
        [0.0004, 0.0006, 0.0012, 0.0022, 0.0210, 0.0025, 0.0016, 0.0012],
        [0.0003, 0.0005, 0.0008, 0.0014, 0.0025, 0.0240, 0.0028, 0.0018],
        [0.0002, 0.0004, 0.0006, 0.0010, 0.0016, 0.0028, 0.0270, 0.0030],
        [0.0001, 0.0003, 0.0005, 0.0008, 0.0012, 0.0018, 0.0030, 0.0300],
    ]

    min_return = params["min_return"]
    max_weight = params["max_weight"]
    budget = params["budget"]

    model = pyo.ConcreteModel()

    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(0.0, max_weight))

    def budget_rule(mdl):
        return sum(mdl.w[i] for i in mdl.assets) == budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def return_rule(mdl):
        return sum(returns[i] * mdl.w[i] for i in mdl.assets) >= min_return

    model.return_con = pyo.Constraint(rule=return_rule)

    # Objective as a proper quadratic expression (needed for HiGHS QP detection)
    quad_expr = sum(
        cov[i][j] * model.w[i] * model.w[j]
        for i in model.assets
        for j in model.assets
    )
    model.obj = pyo.Objective(expr=quad_expr, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}