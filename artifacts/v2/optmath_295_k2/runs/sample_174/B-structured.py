# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":[0,1,2]},"params":{"profit_per_unit":"vector[product]","holding_cost":"scalar or vector[product]","machine_hours_per_unit":"vector[machine], ordered grinders/drills/borers; shared by both products","grinder_capacity":"vector[period], including maintenance","drill_capacity":"vector[period], including maintenance","borer_capacity":"vector[period], including maintenance","inventory_limit":"scalar or vector[product]","sales_limit_product0":"vector[period]","sales_limit_product1":"vector[period]","target_inventory":"scalar or vector[product]"},"variables":{"production[p,t]":"continuous nonnegative","inventory[p,t]":"continuous nonnegative","sales[p,t]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum(machine_hours_per_unit[k] * production[p,t] for p) <= capacity[k,t] for each machine k and period t; capacity rows are grinder_capacity, drill_capacity, borer_capacity","inventory[p,t] <= inventory_limit[p] for each product p and period t","sales[p,t] <= sales_limit_product_p[t] for each product p and period t","inventory[p,3] = target_inventory[p] for each product p"],"objective":"maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost[p] * inventory[p,t] for p,t)","normalization":"Broadcast scalar holding_cost, inventory_limit, and target_inventory across products; otherwise index by product."}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _product_value(value, product):
    """Accept either a numeric scalar or a product-indexed collection."""
    return value if isinstance(value, Number) else value[product]


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    capacities = (grinder_capacity, drill_capacity, borer_capacity)
    sales_limits = (sales_limit_product0, sales_limit_product1)

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 1)
    model.periods = pyo.RangeSet(0, 3)
    model.machines = pyo.RangeSet(0, 2)
    model.later_periods = pyo.RangeSet(1, 3)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(current, product):
        return (
            current.production[product, 0]
            == current.sales[product, 0] + current.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(current, product, period):
        return (
            current.inventory[product, period - 1]
            + current.production[product, period]
            == current.sales[product, period]
            + current.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.later_periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(current, machine, period):
        return (
            sum(
                machine_hours_per_unit[machine]
                * current.production[product, period]
                for product in current.products
            )
            <= capacities[machine][period]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(current, product, period):
        return (
            current.inventory[product, period]
            <= _product_value(inventory_limit, product)
        )

    model.inventory_capacity = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(current, product, period):
        return current.sales[product, period] <= sales_limits[product][period]

    model.sales_capacity = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def target_inventory_rule(current, product):
        return (
            current.inventory[product, 3]
            == _product_value(target_inventory, product)
        )

    model.final_inventory = pyo.Constraint(
        model.products, rule=target_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit_per_unit[product] * model.sales[product, period]
            - _product_value(holding_cost, product)
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}