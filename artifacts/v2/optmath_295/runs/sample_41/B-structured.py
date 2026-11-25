# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3],"machines":[0,1,2]},"params":{"profit_per_unit_sold":"real[product]","inventory_holding_cost":"nonnegative scalar","machine_hours_per_unit":"nonnegative[machine][product]","machine_capacity_per_period":"nonnegative[machine]","inventory_capacity_per_product":"nonnegative scalar or [product]","sales_limit":"nonnegative[product][period]","target_final_inventory":"nonnegative scalar or [product]"},"variables":{"production[product,period]":"continuous nonnegative","sales[product,period]":"continuous nonnegative","inventory[product,period]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p machine_hours_per_unit[k][p]*production[p,t] <= machine_capacity_per_period[k]","inventory[p,t] <= inventory_capacity_per_product[p] (broadcast scalar)","sales[p,t] <= sales_limit[p][t]","inventory[p,3] = target_final_inventory[p] (broadcast scalar)"],"objective":"maximize sum_(p,t) profit_per_unit_sold[p]*sales[p,t] - inventory_holding_cost*inventory[p,t]"}
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    def product_value(values, product):
        return values if isinstance(values, Number) else values[product]

    profits = params["profit_per_unit_sold"]
    holding_cost = params["inventory_holding_cost"]
    hours = params["machine_hours_per_unit"]
    capacities = params["machine_capacity_per_period"]
    inventory_capacities = params["inventory_capacity_per_product"]
    demand_limits = params["sales_limit"]
    final_targets = params["target_final_inventory"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.machines = pyo.RangeSet(0, 2)

    model.profit_per_unit_sold = pyo.Param(
        model.products,
        initialize={product: profits[product] for product in model.products},
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        initialize=holding_cost,
        within=pyo.NonNegativeReals,
    )
    model.machine_hours_per_unit = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product): hours[machine][product]
            for machine in model.machines
            for product in model.products
        },
        within=pyo.NonNegativeReals,
    )
    model.machine_capacity_per_period = pyo.Param(
        model.machines,
        initialize={
            machine: capacities[machine] for machine in model.machines
        },
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity_per_product = pyo.Param(
        model.products,
        initialize={
            product: product_value(inventory_capacities, product)
            for product in model.products
        },
        within=pyo.NonNegativeReals,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): demand_limits[product][period]
            for product in model.products
            for period in model.periods
        },
        within=pyo.NonNegativeReals,
    )
    model.target_final_inventory = pyo.Param(
        model.products,
        initialize={
            product: product_value(final_targets, product)
            for product in model.products
        },
        within=pyo.NonNegativeReals,
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

    def inventory_balance_rule(block, product, period):
        if period == 0:
            return (
                block.production[product, period]
                == block.sales[product, period]
                + block.inventory[product, period]
            )
        return (
            block.inventory[product, period - 1]
            + block.production[product, period]
            == block.sales[product, period]
            + block.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(block, machine, period):
        return (
            sum(
                block.machine_hours_per_unit[machine, product]
                * block.production[product, period]
                for product in block.products
            )
            <= block.machine_capacity_per_period[machine]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )
    model.inventory_capacity_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.inventory[product, period]
            <= block.inventory_capacity_per_product[product]
        ),
    )
    model.sales_limit_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.sales[product, period] <= block.sales_limit[product, period]
        ),
    )
    model.final_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda block, product: (
            block.inventory[product, 3]
            == block.target_final_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit_sold[product] * model.sales[product, period]
            - model.inventory_holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}