import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    model.profit = pyo.Objective(
        expr=params["profit_A"] * model.xA + params["profit_B"] * model.xB,
        sense=pyo.maximize,
    )

    model.time_limit = pyo.Constraint(
        expr=params["assembly_time_A"] * model.xA
        + params["assembly_time_B"] * model.xB
        <= params["weekly_machine_hours"] * 60
    )

    # For every ratio_A_per_5 units of A, at least ratio_B_min units of B:
    # xB >= (ratio_B_min / ratio_A_per_5) * xA
    model.ratio = pyo.Constraint(
        expr=params["ratio_A_per_5"] * model.xB
        >= params["ratio_B_min"] * model.xA
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}