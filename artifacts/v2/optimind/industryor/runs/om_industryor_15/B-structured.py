# IR: {"sets":{"T":[1,2,3],"T0":[0,1,2,3]},"params":{"warehouse_capacity":"nonnegative scalar","initial_inventory":"nonnegative scalar","purchase_price":"monthly real prices","selling_price":"monthly real prices"},"variables":{"purchase[t]":"continuous nonnegative, t in T","sales[t]":"continuous nonnegative, t in T","inventory[t]":"continuous nonnegative, t in T0"},"constraints":["inventory[0] = initial_inventory","inventory[t] = inventory[t-1] + purchase[t] - sales[t], t in T","inventory[t-1] + purchase[t] <= warehouse_capacity, t in T"],"objective":"maximize sum(selling_price[t]*sales[t] - purchase_price[t]*purchase[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Monthly prices may be sequences ordered by month or mappings keyed
    by month numbers 1, 2, 3 (integer or string keys).

    Warehouse capacity applies immediately after beginning-of-month
    purchases. Sales occur afterward. Unsold final inventory has no
    terminal value. Product quantities are continuous.
    """
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    def monthly_value(values, month):
        if isinstance(values, Mapping):
            if month in values:
                return values[month]
            return values[str(month)]
        return values[month - 1]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 3)
    model.inventory_periods = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(
        initialize=warehouse_capacity, within=pyo.NonNegativeReals
    )
    model.starting_stock = pyo.Param(
        initialize=initial_inventory, within=pyo.NonNegativeReals
    )
    model.purchase_cost = pyo.Param(
        model.months,
        initialize=lambda mod, month: monthly_value(purchase_price, month),
        within=pyo.Reals,
    )
    model.sales_price = pyo.Param(
        model.months,
        initialize=lambda mod, month: monthly_value(selling_price, month),
        within=pyo.Reals,
    )

    model.purchase = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(
        model.inventory_periods, domain=pyo.NonNegativeReals
    )

    model.initial_stock_constraint = pyo.Constraint(
        expr=model.inventory[0] == model.starting_stock
    )

    def inventory_balance_rule(mod, month):
        return (
            mod.inventory[month]
            == mod.inventory[month - 1]
            + mod.purchase[month]
            - mod.sales[month]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    def warehouse_limit_rule(mod, month):
        return (
            mod.inventory[month - 1] + mod.purchase[month]
            <= mod.capacity
        )

    model.warehouse_limit = pyo.Constraint(
        model.months, rule=warehouse_limit_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.sales_price[month] * model.sales[month]
            - model.purchase_cost[month] * model.purchase[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when its default solution loading finds
        # no feasible solution. Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}