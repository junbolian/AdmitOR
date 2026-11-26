import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    chairs_per_order_A = params["chairs_per_order_A"]
    chairs_per_order_B = params["chairs_per_order_B"]
    chairs_per_order_C = params["chairs_per_order_C"]
    min_chairs = params["min_chairs"]
    max_chairs = params["max_chairs"]
    min_B_if_A = params["min_B_if_A"]

    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xC = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.yA = pyo.Var(domain=pyo.Binary)
    model.yB = pyo.Var(domain=pyo.Binary)
    model.yC = pyo.Var(domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=cost_A * model.xA + cost_B * model.xB + cost_C * model.xC,
        sense=pyo.minimize,
    )

    model.min_chairs_con = pyo.Constraint(
        expr=chairs_per_order_A * model.xA
        + chairs_per_order_B * model.xB
        + chairs_per_order_C * model.xC
        >= min_chairs
    )
    model.max_chairs_con = pyo.Constraint(
        expr=chairs_per_order_A * model.xA
        + chairs_per_order_B * model.xB
        + chairs_per_order_C * model.xC
        <= max_chairs
    )

    # Big-M linking constraints: xA <= M * yA etc.
    bigM = max(
        (max_chairs // chairs_per_order_A) + 1,
        (max_chairs // chairs_per_order_B) + 1,
        (max_chairs // chairs_per_order_C) + 1,
    )

    model.linkA = pyo.Constraint(expr=model.xA <= bigM * model.yA)
    model.linkB = pyo.Constraint(expr=model.xB <= bigM * model.yB)
    model.linkC = pyo.Constraint(expr=model.xC <= bigM * model.yC)

    # If A is used, at least min_B_if_A chairs from B.
    model.min_B_if_A_con = pyo.Constraint(
        expr=chairs_per_order_B * model.xB >= min_B_if_A * model.yA
    )

    # If B is used, C must be used.
    model.B_requires_C = pyo.Constraint(expr=model.yB <= model.yC)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}