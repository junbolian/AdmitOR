# IR: {"sets":{"T":[7,8,9,10,11,12]},"params":{"buy_price":"T-indexed real","sell_price":"T-indexed real","warehouse_capacity":"nonnegative real","initial_stock":"nonnegative real"},"variables":{"purchase[t]":"nonnegative continuous","sales[t]":"nonnegative continuous","inventory[t]":"nonnegative continuous"},"constraints":["For each t: opening_stock[t] = initial_stock if t=7, else inventory[t-1] (expression).","For each t: opening_stock[t] + purchase[t] <= warehouse_capacity.","For each t: inventory[t] = opening_stock[t] + purchase[t] - sales[t]."],"objective":"Maximize sum(sell_price[t]*sales[t] - buy_price[t]*purchase[t] for t in T)."}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize sales revenue less purchasing costs over July–December.

    Price inputs may be six-element sequences ordered July–December,
    or mappings keyed by month numbers (integers or strings).
    Quantities are continuous; December stock has no terminal value.
    """
    months = tuple(range(7, 13))

    def monthly_values(raw_prices, parameter_name):
        if isinstance(raw_prices, Mapping):
            return {
                month: (
                    raw_prices[month]
                    if month in raw_prices
                    else raw_prices[str(month)]
                )
                for month in months
            }

        values = list(raw_prices)
        if len(values) != len(months):
            raise ValueError(
                f"{parameter_name} must contain one price for each "
                "month from July through December."
            )
        return dict(zip(months, values))

    buy_prices = monthly_values(params["buy_price"], "buy_price")
    sell_prices = monthly_values(params["sell_price"], "sell_price")
    capacity = params["warehouse_capacity"]
    starting_stock = params["initial_stock"]

    model = pyo.ConcreteModel()
    model.months = pyo.Set(initialize=months, ordered=True)

    model.buy_price = pyo.Param(
        model.months, initialize=buy_prices, within=pyo.Reals
    )
    model.sell_price = pyo.Param(
        model.months, initialize=sell_prices, within=pyo.Reals
    )
    model.warehouse_capacity = pyo.Param(
        initialize=capacity, within=pyo.NonNegativeReals
    )
    model.initial_stock = pyo.Param(
        initialize=starting_stock, within=pyo.NonNegativeReals
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def opening_stock_rule(instance, month):
        if month == months[0]:
            return instance.initial_stock
        return instance.inventory[month - 1]

    model.opening_stock = pyo.Expression(
        model.months, rule=opening_stock_rule
    )

    def capacity_rule(instance, month):
        return (
            instance.opening_stock[month] + instance.purchase[month]
            <= instance.warehouse_capacity
        )

    model.storage_limit = pyo.Constraint(
        model.months, rule=capacity_rule
    )

    def inventory_balance_rule(instance, month):
        return instance.inventory[month] == (
            instance.opening_stock[month]
            + instance.purchase[month]
            - instance.sales[month]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.sell_price[month] * model.sales[month]
            - model.buy_price[month] * model.purchase[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}