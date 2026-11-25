# IR: {"sets":{"P":["product_0","product_1","product_2","product_3"],"T":[0,1,2,3,4,5]},"params":{"profit":"P","holding_cost":"scalar","grinder_capacity":"scalar or T","drill_capacity":"scalar or T","borer_capacity":"scalar or T; effective capacity is zero at t=3","grinder_time":"P","drill_time":"P","borer_time":"P","inventory_limit":"scalar or P","sales_limit":"P x T","target_inventory":"scalar or P"},"variables":{"production[P,T]":"continuous nonnegative","sales[P,T]":"continuous nonnegative","inventory[P,T]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p grinder_time[p]*production[p,t] <= grinder_capacity[t]","sum_p drill_time[p]*production[p,t] <= drill_capacity[t]","sum_p borer_time[p]*production[p,t] <= (0 if t=3 else borer_capacity[t])","inventory[p,t] <= inventory_limit[p]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = target_inventory[p]"],"objective":"maximize sum_(p,t) profit[p]*sales[p,t] - holding_cost*inventory[p,t]"}
from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, label):
    """Read a scalar, positional sequence, or labeled/indexed mapping."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        if position in data:
            return data[position]
        return data[str(position)]
    if isinstance(data, Number):
        return data
    return data[position]


def solve(params):
    products = tuple(f"product_{position}" for position in range(4))
    periods = tuple(range(6))
    product_position = {
        product: position for position, product in enumerate(products)
    }

    profit_data = params["profit"]
    holding_cost_data = params["holding_cost"]
    grinder_capacity_data = params["grinder_capacity"]
    drill_capacity_data = params["drill_capacity"]
    borer_capacity_data = params["borer_capacity"]
    grinder_time_data = params["grinder_time"]
    drill_time_data = params["drill_time"]
    borer_time_data = params["borer_time"]
    inventory_limit_data = params["inventory_limit"]
    sales_limit_data = params["sales_limit"]
    target_inventory_data = params["target_inventory"]

    def product_values(data):
        return {
            product: _entry(data, product_position[product], product)
            for product in products
        }

    def period_values(data):
        return {
            period: _entry(data, period, f"period_{period}")
            for period in periods
        }

    sales_limits = {}
    for product in products:
        row = _entry(sales_limit_data, product_position[product], product)
        for period in periods:
            sales_limits[product, period] = _entry(
                row, period, f"period_{period}"
            )

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.periods = pyo.Set(initialize=periods, ordered=True)

    model.profit = pyo.Param(
        model.products, initialize=product_values(profit_data)
    )
    model.holding_cost = pyo.Param(initialize=holding_cost_data)

    model.grinder_capacity = pyo.Param(
        model.periods, initialize=period_values(grinder_capacity_data)
    )
    model.drill_capacity = pyo.Param(
        model.periods, initialize=period_values(drill_capacity_data)
    )
    model.borer_capacity = pyo.Param(
        model.periods, initialize=period_values(borer_capacity_data)
    )

    model.grinder_time = pyo.Param(
        model.products, initialize=product_values(grinder_time_data)
    )
    model.drill_time = pyo.Param(
        model.products, initialize=product_values(drill_time_data)
    )
    model.borer_time = pyo.Param(
        model.products, initialize=product_values(borer_time_data)
    )
    model.inventory_limit = pyo.Param(
        model.products, initialize=product_values(inventory_limit_data)
    )
    model.sales_limit = pyo.Param(
        model.products, model.periods, initialize=sales_limits
    )
    model.target_inventory = pyo.Param(
        model.products, initialize=product_values(target_inventory_data)
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, product, period):
        if period == 0:
            return (
                instance.production[product, period]
                == instance.sales[product, period]
                + instance.inventory[product, period]
            )
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def grinder_rule(instance, period):
        return sum(
            instance.grinder_time[product]
            * instance.production[product, period]
            for product in instance.products
        ) <= instance.grinder_capacity[period]

    def drill_rule(instance, period):
        return sum(
            instance.drill_time[product]
            * instance.production[product, period]
            for product in instance.products
        ) <= instance.drill_capacity[period]

    def borer_rule(instance, period):
        effective_capacity = (
            0 if period == 3 else instance.borer_capacity[period]
        )
        return sum(
            instance.borer_time[product]
            * instance.production[product, period]
            for product in instance.products
        ) <= effective_capacity

    model.grinder_usage = pyo.Constraint(model.periods, rule=grinder_rule)
    model.drill_usage = pyo.Constraint(model.periods, rule=drill_rule)
    model.borer_usage = pyo.Constraint(model.periods, rule=borer_rule)

    model.inventory_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= instance.inventory_limit[product]
        ),
    )
    model.sales_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        ),
    )
    model.ending_inventory = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 5]
            == instance.target_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}