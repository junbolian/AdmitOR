# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit":["profit_per_unit_product0","profit_per_unit_product1"],"holding_cost":"holding_cost_per_unit_per_period","hours":{"grinder":["grinder_hours_product0","grinder_hours_product1"],"drill":["drill_hours_product0","drill_hours_product1"],"borer":["borer_hours_product0","borer_hours_product1"]},"capacity":{"grinder":"grinder_capacity_per_period","drill":"drill_capacity_per_period","borer":"borer_capacity_per_period"},"max_inventory":["max_inventory_product0","max_inventory_product1"],"sales_limit":["sales_limit_product0","sales_limit_product1"],"target_inventory":["target_inventory_product0","target_inventory_product1"]},"variables":{"production[p,t]":"continuous nonnegative","inventory[p,t]":"continuous nonnegative","sales[p,t]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for all p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for all p,t>0","sum(hours[r,p]*production[p,t] for p) <= capacity[r] for all r,t","inventory[p,t] <= max_inventory[p] for all p,t","sales[p,t] <= sales_limit[p][t] for all p,t","inventory[p,3] = target_inventory[p] for all p"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Sales-limit parameters must be sequences or mappings indexed by period."""
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
    model.machine_hours = pyo.Param(
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
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize={
            "grinder": params["grinder_capacity_per_period"],
            "drill": params["drill_capacity_per_period"],
            "borer": params["borer_capacity_per_period"],
        },
    )
    model.inventory_limit = pyo.Param(
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
    model.terminal_target = pyo.Param(
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

    def capacity_rule(instance, machine, period):
        return (
            sum(
                instance.machine_hours[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.machine_capacity[machine]
        )

    model.capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )
    model.inventory_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= instance.inventory_limit[product]
        ),
    )
    model.sales_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 3]
            == instance.terminal_target[product]
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
    except RuntimeError:
        # APPsi can raise when no solution is available to load.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}