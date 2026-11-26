import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_disposed = pyo.Var(domain=pyo.NonNegativeReals)

    model.front = pyo.Constraint(
        expr=params["a_front_hours"] * model.xA
        + params["b_front_hours"] * model.xB
        <= params["front_capacity"]
    )
    model.back = pyo.Constraint(
        expr=params["a_back_hours"] * model.xA
        + params["b_back_hours"] * model.xB
        <= params["back_capacity"]
    )

    model.c_balance = pyo.Constraint(
        expr=model.c_sold + model.c_disposed
        == params["c_per_b"] * model.xB
    )
    model.c_sell_limit = pyo.Constraint(
        expr=model.c_sold <= params["c_sellable_max"]
    )

    model.profit = pyo.Objective(
        expr=params["profit_a"] * model.xA
        + params["profit_b"] * model.xB
        + params["profit_c"] * model.c_sold
        - params["c_disposal_cost"] * model.c_disposed,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}