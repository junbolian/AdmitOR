# IR: {"sets":{"products":["table","chair","bookshelf"]},"params":["sell_table","sell_chair","sell_bookshelf","cost_table","cost_chair","cost_bookshelf","space_table","space_chair","space_bookshelf","space_capacity","min_tables","min_bookshelves","max_items"],"variables":{"production[products]":"nonnegative integer"},"constraints":["sum(space[p]*production[p] for p in products) <= space_capacity","production[table] >= min_tables","production[bookshelf] >= min_bookshelves","sum(production[p] for p in products) <= max_items"],"objective":"maximize sum((sell[p]-cost[p])*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(
        initialize=["table", "chair", "bookshelf"],
        ordered=True,
    )

    model.sell = pyo.Param(
        model.products,
        initialize={
            "table": params["sell_table"],
            "chair": params["sell_chair"],
            "bookshelf": params["sell_bookshelf"],
        },
    )
    model.cost = pyo.Param(
        model.products,
        initialize={
            "table": params["cost_table"],
            "chair": params["cost_chair"],
            "bookshelf": params["cost_bookshelf"],
        },
    )
    model.space = pyo.Param(
        model.products,
        initialize={
            "table": params["space_table"],
            "chair": params["space_chair"],
            "bookshelf": params["space_bookshelf"],
        },
    )
    model.space_capacity = pyo.Param(initialize=params["space_capacity"])
    model.min_tables = pyo.Param(initialize=params["min_tables"])
    model.min_bookshelves = pyo.Param(initialize=params["min_bookshelves"])
    model.max_items = pyo.Param(initialize=params["max_items"])

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeIntegers,
    )

    model.warehouse_limit = pyo.Constraint(
        expr=sum(
            model.space[product] * model.production[product]
            for product in model.products
        ) <= model.space_capacity
    )
    model.table_minimum = pyo.Constraint(
        expr=model.production["table"] >= model.min_tables
    )
    model.bookshelf_minimum = pyo.Constraint(
        expr=model.production["bookshelf"] >= model.min_bookshelves
    )
    model.total_item_limit = pyo.Constraint(
        expr=sum(
            model.production[product] for product in model.products
        ) <= model.max_items
    )

    model.profit = pyo.Objective(
        expr=sum(
            (model.sell[product] - model.cost[product])
            * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}