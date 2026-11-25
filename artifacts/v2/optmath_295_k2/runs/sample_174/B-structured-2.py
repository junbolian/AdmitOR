# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinders","drills","borers"]},"params":{"profit_per_unit":"[product]","holding_cost":"scalar or [product]","machine_hours_per_unit":"[machine] or [machine][product]; machine order grinders, drills, borers","grinder_capacity":"[period]","drill_capacity":"[period]","borer_capacity":"[period]","inventory_limit":"scalar or [product]","sales_limit_product0":"[period]","sales_limit_product1":"[period]","target_inventory":"scalar or [product]"},"variables":{"production[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum_p machine_hours_per_unit[k,p]*production[p,t] <= capacity[k,t] for each machine k and period t","inventory[p,t] <= inventory_limit[p] for each product p and period t","sales[0,t] <= sales_limit_product0[t] for each period t","sales[1,t] <= sales_limit_product1[t] for each period t","inventory[p,3] = target_inventory[p] for each product p"],"objective":"maximize sum_(p,t) (profit_per_unit[p]*sales[p,t] - holding_cost[p]*inventory[p,t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, key):
    """Read an integer/string-keyed mapping or an indexed sequence."""
    if isinstance(data, Mapping):
        if key in data:
            return data[key]
        return data[str(key)]
    return data[key]


def _product_value(data, product):
    """Broadcast a scalar or extract one product's scalar value."""
    if isinstance(data, Mapping):
        return _indexed(data, product)
    if getattr(data, "ndim", None) == 0:
        return data.item()
    if hasattr(data, "__getitem__") and not isinstance(data, (str, bytes)):
        return _indexed(data, product)
    return data


def _machine_data(data, machine, position):
    """Accept machine-name mappings or positional machine sequences."""
    if isinstance(data, Mapping) and machine in data:
        return data[machine]
    return _indexed(data, position)


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinders", "drills", "borers"], ordered=True
    )

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: _indexed(params["profit_per_unit"], product)
            for product in model.products
        },
    )
    model.holding_cost = pyo.Param(
        model.products,
        initialize={
            product: _product_value(params["holding_cost"], product)
            for product in model.products
        },
    )
    model.machine_hours_per_unit = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product): _product_value(
                _machine_data(
                    params["machine_hours_per_unit"], machine, position
                ),
                product,
            )
            for position, machine in enumerate(model.machines)
            for product in model.products
        },
    )

    capacity_inputs = {
        "grinders": params["grinder_capacity"],
        "drills": params["drill_capacity"],
        "borers": params["borer_capacity"],
    }
    model.machine_capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): _indexed(capacity_inputs[machine], period)
            for machine in model.machines
            for period in model.periods
        },
    )
    model.inventory_limit = pyo.Param(
        model.products,
        initialize={
            product: _product_value(params["inventory_limit"], product)
            for product in model.products
        },
    )
    sales_inputs = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): _indexed(sales_inputs[product], period)
            for product in model.products
            for period in model.periods
        },
    )
    model.target_inventory = pyo.Param(
        model.products,
        initialize={
            product: _product_value(params["target_inventory"], product)
            for product in model.products
        },
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

    def inventory_balance_rule(factory, product, period):
        if period == 0:
            return (
                factory.production[product, period]
                == factory.sales[product, period]
                + factory.inventory[product, period]
            )
        return (
            factory.inventory[product, period - 1]
            + factory.production[product, period]
            == factory.sales[product, period]
            + factory.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(factory, machine, period):
        return (
            sum(
                factory.machine_hours_per_unit[machine, product]
                * factory.production[product, period]
                for product in factory.products
            )
            <= factory.machine_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )
    model.inventory_upper_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda factory, product, period: (
            factory.inventory[product, period]
            <= factory.inventory_limit[product]
        ),
    )
    model.sales_upper_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda factory, product, period: (
            factory.sales[product, period]
            <= factory.sales_limit[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda factory, product: (
            factory.inventory[product, 3]
            == factory.target_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost[product] * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}