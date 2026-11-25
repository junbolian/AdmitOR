# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4,5]},"params":{"profit_per_unit":"vector[products]","holding_cost_per_unit":"scalar","grinder_hours_per_unit":"vector[products]","drill_hours_per_unit":"vector[products]","borer_hours_per_unit":"vector[products]","grinder_capacity_per_period":"scalar","drill_capacity_per_period":"scalar; effective capacity is 0 in period 2","borer_capacity_per_period":"scalar","max_inventory_per_product":"scalar","max_sales_product_0":"vector[periods]","max_sales_product_1":"vector[periods]","max_sales_product_2":"vector[periods]","terminal_inventory_target":"scalar"},"variables":{"production[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals"},"constraints":{"initial_balance":"production[p,0] == sales[p,0] + inventory[p,0]","later_balance":"inventory[p,t-1] + production[p,t] == sales[p,t] + inventory[p,t] for t > 0","grinder_capacity":"sum(grinder_hours_per_unit[p]*production[p,t] for p) <= grinder_capacity_per_period","drill_capacity":"sum(drill_hours_per_unit[p]*production[p,t] for p) <= (0 if t == 2 else drill_capacity_per_period)","borer_capacity":"sum(borer_hours_per_unit[p]*production[p,t] for p) <= borer_capacity_per_period","inventory_limit":"inventory[p,t] <= max_inventory_per_product","sales_limit":"sales[p,t] <= max_sales_product_p[t]","terminal_inventory":"inventory[p,5] == terminal_inventory_target"},"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit*inventory[p,t] for p,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 5)
    model.later_periods = pyo.RangeSet(1, 5)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost_per_unit = pyo.Param(
        initialize=params["holding_cost_per_unit"]
    )
    model.grinder_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["grinder_hours_per_unit"][product],
    )
    model.drill_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["drill_hours_per_unit"][product],
    )
    model.borer_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["borer_hours_per_unit"][product],
    )
    model.grinder_capacity_per_period = pyo.Param(
        initialize=params["grinder_capacity_per_period"]
    )
    model.drill_capacity_per_period = pyo.Param(
        initialize=params["drill_capacity_per_period"]
    )
    model.borer_capacity_per_period = pyo.Param(
        initialize=params["borer_capacity_per_period"]
    )
    model.max_inventory_per_product = pyo.Param(
        initialize=params["max_inventory_per_product"]
    )
    model.terminal_inventory_target = pyo.Param(
        initialize=params["terminal_inventory_target"]
    )

    sales_limits = {
        0: params["max_sales_product_0"],
        1: params["max_sales_product_1"],
        2: params["max_sales_product_2"],
    }
    model.sales_limit_per_period = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: sales_limits[product][period],
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    model.initial_balance = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        ),
    )
    model.later_balance = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period - 1] + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        ),
    )

    model.grinder_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.grinder_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.grinder_capacity_per_period
        ),
    )
    model.drill_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.drill_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= (0 if period == 2 else mdl.drill_capacity_per_period)
        ),
    )
    model.borer_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.borer_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.borer_capacity_per_period
        ),
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.max_inventory_per_product
        ),
    )
    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period]
            <= mdl.sales_limit_per_period[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 5] == mdl.terminal_inventory_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_profit))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}