import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.t = pyo.Var(domain=pyo.NonNegativeReals)
    model.c = pyo.Var(domain=pyo.NonNegativeReals)
    model.b = pyo.Var(domain=pyo.NonNegativeReals)

    profit_table = params["price_table"] - params["cost_table"]
    profit_chair = params["price_chair"] - params["cost_chair"]
    profit_bookshelf = params["price_bookshelf"] - params["cost_bookshelf"]

    model.obj = pyo.Objective(
        expr=profit_table * model.t + profit_chair * model.c + profit_bookshelf * model.b,
        sense=pyo.maximize,
    )

    model.space_con = pyo.Constraint(
        expr=params["space_table"] * model.t
        + params["space_chair"] * model.c
        + params["space_bookshelf"] * model.b
        <= params["space_capacity"]
    )

    model.min_tables_con = pyo.Constraint(expr=model.t >= params["min_tables"])
    model.min_bookshelves_con = pyo.Constraint(expr=model.b >= params["min_bookshelves"])

    model.total_items_con = pyo.Constraint(
        expr=model.t + model.c + model.b <= params["max_total_items"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}