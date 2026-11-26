# IR: {"sets":{"T":[1,2,3]},"params":{"initial_inventory":"nonnegative scalar","warehouse_capacity":"nonnegative scalar","purchase_price":"real vector indexed by T","selling_price":"real vector indexed by T"},"variables":{"purchase[t]":"nonnegative continuous","sales[t]":"nonnegative continuous","inventory[t]":"nonnegative continuous"},"constraints":["inventory[1] = initial_inventory + purchase[1] - sales[1]","inventory[t] = inventory[t-1] + purchase[t] - sales[t] for t in {2,3}","initial_inventory + purchase[1] <= warehouse_capacity","inventory[t-1] + purchase[t] <= warehouse_capacity for t in {2,3}"],"objective":"maximize sum(selling_price[t]*sales[t] - purchase_price[t]*purchase[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the quarterly procurement and sales LP.

    Price inputs may be three-element sequences ordered by month or mappings
    keyed by months 1, 2, 3 (integer keys or string keys).
    Warehouse capacity applies immediately after each monthly purchase.
    """

    def monthly_value(values, month):
        if isinstance(values, Mapping):
            if month in values:
                return values[month]
            return values[str(month)]
        return values[month - 1]

    initial_inventory = params["initial_inventory"]
    warehouse_capacity = params["warehouse_capacity"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 3)

    model.initial_stock = pyo.Param(
        initialize=initial_inventory,
        within=pyo.NonNegativeReals,
    )
    model.storage_limit = pyo.Param(
        initialize=warehouse_capacity,
        within=pyo.NonNegativeReals,
    )
    model.purchase_cost = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(purchase_price, month)
            for month in model.months
        },
        within=pyo.Reals,
    )
    model.sale_revenue = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(selling_price, month)
            for month in model.months
        },
        within=pyo.Reals,
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(instance, month):
        opening_stock = (
            instance.initial_stock
            if month == 1
            else instance.inventory[month - 1]
        )
        return (
            instance.inventory[month]
            == opening_stock + instance.purchase[month] - instance.sales[month]
        )

    model.stock_balance = pyo.Constraint(
        model.months,
        rule=inventory_balance_rule,
    )

    def warehouse_capacity_rule(instance, month):
        opening_stock = (
            instance.initial_stock
            if month == 1
            else instance.inventory[month - 1]
        )
        return (
            opening_stock + instance.purchase[month]
            <= instance.storage_limit
        )

    model.storage_capacity = pyo.Constraint(
        model.months,
        rule=warehouse_capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.sale_revenue[month] * model.sales[month]
            - model.purchase_cost[month] * model.purchase[month]
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