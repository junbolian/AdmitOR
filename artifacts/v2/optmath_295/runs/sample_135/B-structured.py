# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit[p]":"params[profit_per_unit_product{p}]","holding_cost":"params[holding_cost_per_unit_per_period]","capacity[k,t]":"params[{k}_capacity_per_period][t]","hours[k,p]":"params[{k}_hours_product{p}]","inventory_limit":"params[max_inventory_per_product_per_period]","sales_limit[p,t]":"params[max_sales_product{p}_per_period][t]","terminal_inventory[p]":"params[terminal_inventory_product{p}]"},"variables":{"production[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each p and t>0","sum_p hours[k,p]*production[p,t] <= capacity[k,t] for each k,t","inventory[p,t] <= inventory_limit for each p,t","sales[p,t] <= sales_limit[p,t] for each p,t","inventory[p,3] = terminal_inventory[p] for each p"],"objective":"maximize sum_{p,t}(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous production, inventory, and sales planning problem."""
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.profit = pyo.Param(
        model.products,
        initialize={
            0: params["profit_per_unit_product0"],
            1: params["profit_per_unit_product1"],
        },
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"]
    )

    capacity_data = {
        "grinder": params["grinder_capacity_per_period"],
        "drill": params["drill_capacity_per_period"],
        "borer": params["borer_capacity_per_period"],
    }
    model.capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): capacity_data[machine][period]
            for machine in model.machines
            for period in model.periods
        },
    )

    model.hours = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grinder", 0): params["grinder_hours_product0"],
            ("grinder", 1): params["grinder_hours_product1"],
            ("drill", 0): params["drill_hours_product0"],
            ("drill", 1): params["drill_hours_product1"],
            ("borer", 0): params["borer_hours_product0"],
            ("borer", 1): params["borer_hours_product1"],
        },
    )
    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory_per_product_per_period"]
    )

    sales_data = {
        0: params["max_sales_product0_per_period"],
        1: params["max_sales_product1_per_period"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_data[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.terminal_inventory = pyo.Param(
        model.products,
        initialize={
            0: params["terminal_inventory_product0"],
            1: params["terminal_inventory_product1"],
        },
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

    def inventory_balance_rule(model, product, period):
        if period == 0:
            return (
                model.production[product, period]
                == model.sales[product, period]
                + model.inventory[product, period]
            )
        return (
            model.inventory[product, period - 1]
            + model.production[product, period]
            == model.sales[product, period]
            + model.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(model, machine, period):
        return (
            sum(
                model.hours[machine, product]
                * model.production[product, period]
                for product in model.products
            )
            <= model.capacity[machine, period]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_capacity_rule(model, product, period):
        return (
            model.inventory[product, period] <= model.inventory_limit
        )

    model.inventory_capacity = pyo.Constraint(
        model.products, model.periods, rule=inventory_capacity_rule
    )

    def sales_capacity_rule(model, product, period):
        return (
            model.sales[product, period]
            <= model.sales_limit[product, period]
        )

    model.sales_capacity = pyo.Constraint(
        model.products, model.periods, rule=sales_capacity_rule
    )

    def terminal_inventory_rule(model, product):
        return (
            model.inventory[product, 3]
            == model.terminal_inventory[product]
        )

    model.terminal_requirement = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
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
    except RuntimeError:
        # APPSI raises when it cannot load a feasible solution.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}