# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":["profit_per_unit_product0","profit_per_unit_product1","holding_cost_per_unit_per_period","grinder_hours_product0","grinder_hours_product1","grinder_capacity_per_period","drill_hours_product0","drill_hours_product1","drill_capacity_per_period","borer_hours_product0","borer_hours_product1","borer_capacity_per_period","max_inventory_product0","max_inventory_product1","sales_limit_product0","sales_limit_product1","target_inventory_product0","target_inventory_product1"],"variables":{"production[p,t]":"continuous >= 0","inventory[p,t]":"continuous >= 0","sales[p,t]":"continuous >= 0"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and t in {1,2,3}","sum(hours[r,p]*production[p,t] for p in products) <= capacity[r] for each machine r and period t","inventory[p,t] <= max_inventory[p] for each product p and period t","sales[p,t] <= sales_limit[p,t] for each product p and period t","inventory[p,3] = target_inventory[p] for each product p"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p in products for t in periods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Build and solve the continuous production and inventory model.

    Each sales_limit_product parameter must support indexing by periods 0–3.
    """
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.later_periods = pyo.Set(initialize=[1, 2, 3], ordered=True)
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
    model.capacity = pyo.Param(
        model.machines,
        initialize={
            "grinder": params["grinder_capacity_per_period"],
            "drill": params["drill_capacity_per_period"],
            "borer": params["borer_capacity_per_period"],
        },
    )
    model.max_inventory = pyo.Param(
        model.products,
        initialize={
            0: params["max_inventory_product0"],
            1: params["max_inventory_product1"],
        },
    )

    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.target_inventory = pyo.Param(
        model.products,
        initialize={
            0: params["target_inventory_product0"],
            1: params["target_inventory_product1"],
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

    def initial_balance_rule(model, product):
        return (
            model.production[product, 0]
            == model.sales[product, 0] + model.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(model, product, period):
        return (
            model.inventory[product, period - 1]
            + model.production[product, period]
            == model.sales[product, period] + model.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=inventory_balance_rule,
    )

    def machine_capacity_rule(model, machine, period):
        return (
            sum(
                model.hours[machine, product]
                * model.production[product, period]
                for product in model.products
            )
            <= model.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(model, product, period):
        return (
            model.inventory[product, period]
            <= model.max_inventory[product]
        )

    model.inventory_limit = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(model, product, period):
        return model.sales[product, period] <= model.sales_limit[product, period]

    model.sales_bound = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def terminal_inventory_rule(model, product):
        return model.inventory[product, 3] == model.target_inventory[product]

    model.terminal_inventory = pyo.Constraint(
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
        # APPsi raises RuntimeError when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}