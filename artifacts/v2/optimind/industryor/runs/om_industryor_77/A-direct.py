import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.table = pyo.Var(domain=pyo.NonNegativeReals)
    model.chair = pyo.Var(domain=pyo.NonNegativeReals)
    model.bookshelf = pyo.Var(domain=pyo.NonNegativeReals)

    profit_table = params["sell_table"] - params["cost_table"]
    profit_chair = params["sell_chair"] - params["cost_chair"]
    profit_bookshelf = params["sell_bookshelf"] - params["cost_bookshelf"]

    model.profit = pyo.Objective(
        expr=(
            profit_table * model.table
            + profit_chair * model.chair
            + profit_bookshelf * model.bookshelf
        ),
        sense=pyo.maximize,
    )

    model.space_con = pyo.Constraint(
        expr=(
            params["space_table"] * model.table
            + params["space_chair"] * model.chair
            + params["space_bookshelf"] * model.bookshelf
            <= params["space_capacity"]
        )
    )

    model.min_tables_con = pyo.Constraint(
        expr=model.table >= params["min_tables"]
    )

    model.min_bookshelves_con = pyo.Constraint(
        expr=model.bookshelf >= params["min_bookshelves"]
    )

    model.max_items_con = pyo.Constraint(
        expr=model.table + model.chair + model.bookshelf <= params["max_items"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}