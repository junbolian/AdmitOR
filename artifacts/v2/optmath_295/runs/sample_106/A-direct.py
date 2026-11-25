import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    returns = params["returns"]
    min_return = params["min_return"]
    weight_sum_target = params["weight_sum_target"]
    weight_upper_bound = params["weight_upper_bound"]
    weight_lower_bound = params["weight_lower_bound"]

    n = 4

    model = pyo.ConcreteModel()

    model.assets = pyo.RangeSet(0, n - 1)

    model.w = pyo.Var(model.assets, bounds=(weight_lower_bound, weight_upper_bound))

    # Objective: minimize portfolio variance (direct quadratic form in weights)
    model.obj = pyo.Objective(
        expr=sum(model.w[i] ** 2 for i in model.assets),
        sense=pyo.minimize,
    )

    # Budget constraint: sum of weights equals target allocation
    model.budget = pyo.Constraint(
        expr=sum(model.w[i] for i in model.assets) == weight_sum_target
    )

    # Minimum return constraint
    model.return_con = pyo.Constraint(
        expr=sum(returns[i] * model.w[i] for i in model.assets) >= min_return
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}