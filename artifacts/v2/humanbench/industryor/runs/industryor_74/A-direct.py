import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    cap_A = params["capacity_A"]
    cap_B = params["capacity_B"]
    cap_C = params["capacity_C"]
    min_chairs = params["min_chairs"]
    max_chairs = params["max_chairs"]
    min_B_if_A = params["min_B_if_A"]

    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xC = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.yA = pyo.Var(domain=pyo.Binary)
    model.yB = pyo.Var(domain=pyo.Binary)

    # Total chairs bounds
    total_chairs = cap_A * model.xA + cap_B * model.xB + cap_C * model.xC
    model.chairs_min = pyo.Constraint(expr=total_chairs >= min_chairs)
    model.chairs_max = pyo.Constraint(expr=total_chairs <= max_chairs)

    # Big-M linking constraints
    bigM = max_chairs

    # If A is ordered, at least min_B_if_A chairs from B
    model.ifA_then_B = pyo.Constraint(
        expr=cap_B * model.xB >= min_B_if_A * model.yA
    )
    # xA > 0 => yA = 1
    model.xA_upper = pyo.Constraint(expr=model.xA <= bigM * model.yA)
    model.xA_lower = pyo.Constraint(expr=model.xA >= model.yA)

    # If B ordered, at least one C order (i.e., xC >= 1)
    model.xB_upper = pyo.Constraint(expr=model.xB <= bigM * model.yB)
    model.xB_lower = pyo.Constraint(expr=model.xB >= model.yB)
    model.ifB_then_C = pyo.Constraint(expr=model.xC >= model.yB)

    model.obj = pyo.Objective(
        expr=cost_A * cap_A * model.xA
        + cost_B * cap_B * model.xB
        + cost_C * cap_C * model.xC,
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}