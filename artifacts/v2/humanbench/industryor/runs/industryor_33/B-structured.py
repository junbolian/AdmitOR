# IR: {"sets":{"T":[1,2,3],"T0":[0,1,2,3]},"params":["warehouse_capacity","initial_stock","initial_capital","purchase_price[t]","selling_price[t]","terminal_stock_requirement"],"variables":{"buy[t]":"continuous nonnegative, t in T","sell[t]":"continuous nonnegative, t in T","stock[t]":"continuous nonnegative, t in T0","cash[t]":"continuous nonnegative, t in T0"},"constraints":["stock[0] = initial_stock","cash[0] = initial_capital","stock[t] <= warehouse_capacity, t in T0","sell[t] <= stock[t-1], t in T","stock[t] = stock[t-1] + buy[t] - sell[t], t in T","cash[t] = cash[t-1] + selling_price[t]*sell[t] - purchase_price[t]*buy[t], t in T","stock[3] = terminal_stock_requirement"],"objective":"maximize sum(selling_price[t]*sell[t] - purchase_price[t]*buy[t] for t in T)","timing":"Sales use beginning-of-month stock; sales receipts may fund same-month purchases; sales may precede deliveries, so warehouse capacity applies to beginning and ending stock."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Prices accept three-element sequences or mappings keyed by 1, 2, 3
    (integer keys or their string equivalents). Profit is trading revenue
    minus purchasing expenditure; ending inventory is held without liquidation.
    """
    purchase_data = params["purchase_price"]
    selling_data = params["selling_price"]

    def monthly_value(data, month):
        if isinstance(data, Mapping):
            if month in data:
                return data[month]
            return data[str(month)]
        return data[month - 1]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 3)
    model.periods = pyo.RangeSet(0, 3)

    model.warehouse_capacity = pyo.Param(
        initialize=params["warehouse_capacity"]
    )
    model.initial_stock = pyo.Param(
        initialize=params["initial_stock"]
    )
    model.initial_capital = pyo.Param(
        initialize=params["initial_capital"]
    )
    model.purchase_price = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(purchase_data, month)
            for month in model.months
        },
    )
    model.selling_price = pyo.Param(
        model.months,
        initialize={
            month: monthly_value(selling_data, month)
            for month in model.months
        },
    )
    model.terminal_stock_requirement = pyo.Param(
        initialize=params["terminal_stock_requirement"]
    )

    model.buy = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.stock = pyo.Var(model.periods, domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.periods, domain=pyo.NonNegativeReals)

    model.starting_stock_constraint = pyo.Constraint(
        expr=model.stock[0] == model.initial_stock
    )
    model.starting_cash_constraint = pyo.Constraint(
        expr=model.cash[0] == model.initial_capital
    )

    def capacity_rule(instance, period):
        return instance.stock[period] <= instance.warehouse_capacity

    model.storage_capacity_constraints = pyo.Constraint(
        model.periods, rule=capacity_rule
    )

    def sales_availability_rule(instance, month):
        return instance.sell[month] <= instance.stock[month - 1]

    model.sales_availability_constraints = pyo.Constraint(
        model.months, rule=sales_availability_rule
    )

    def stock_balance_rule(instance, month):
        return instance.stock[month] == (
            instance.stock[month - 1]
            + instance.buy[month]
            - instance.sell[month]
        )

    model.stock_balance_constraints = pyo.Constraint(
        model.months, rule=stock_balance_rule
    )

    def cash_balance_rule(instance, month):
        return instance.cash[month] == (
            instance.cash[month - 1]
            + instance.selling_price[month] * instance.sell[month]
            - instance.purchase_price[month] * instance.buy[month]
        )

    model.cash_balance_constraints = pyo.Constraint(
        model.months, rule=cash_balance_rule
    )

    model.ending_stock_constraint = pyo.Constraint(
        expr=model.stock[3] == model.terminal_stock_requirement
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.selling_price[month] * model.sell[month]
            - model.purchase_price[month] * model.buy[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined solely by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}