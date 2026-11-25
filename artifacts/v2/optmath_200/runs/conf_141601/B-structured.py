# IR: {"sets":{"P":[0,1],"T":[0,1,2,3],"R":["grinder","drill","borer"]},"params":{"profit_per_unit_0":"scalar","profit_per_unit_1":"scalar","holding_cost_per_unit":"scalar","grinder_hours_per_unit_0":"scalar","grinder_hours_per_unit_1":"scalar","drill_hours_per_unit_0":"scalar","drill_hours_per_unit_1":"scalar","borer_hours_per_unit_0":"scalar","borer_hours_per_unit_1":"scalar","grinder_capacity":"indexed by T","drill_capacity":"indexed by T","borer_capacity":"indexed by T","max_inventory_per_product":"scalar","max_sales_product_0":"indexed by T","max_sales_product_1":"indexed by T","terminal_inventory_per_product":"scalar"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in {1,2,3}","sum(hours[r,p]*production[p,t] for p in P) <= capacity[r,t] for r in R, t in T","inventory[p,t] <= max_inventory_per_product for p in P, t in T","sales[p,t] <= max_sales_product_p[t] for p in P, t in T","inventory[p,3] = terminal_inventory_per_product for p in P"],"objective":"maximize sum(profit_per_unit_p*sales[p,t] - holding_cost_per_unit*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.resources = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    profits = {
        0: params["profit_per_unit_0"],
        1: params["profit_per_unit_1"],
    }
    hours = {
        ("grinder", 0): params["grinder_hours_per_unit_0"],
        ("grinder", 1): params["grinder_hours_per_unit_1"],
        ("drill", 0): params["drill_hours_per_unit_0"],
        ("drill", 1): params["drill_hours_per_unit_1"],
        ("borer", 0): params["borer_hours_per_unit_0"],
        ("borer", 1): params["borer_hours_per_unit_1"],
    }
    capacities = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }
    sales_limits = {
        0: params["max_sales_product_0"],
        1: params["max_sales_product_1"],
    }

    model.unit_profit = pyo.Param(model.products, initialize=profits)
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit"]
    )
    model.machine_hours = pyo.Param(
        model.resources, model.products, initialize=hours
    )
    model.machine_capacity = pyo.Param(
        model.resources,
        model.periods,
        initialize={
            (resource, period): capacities[resource][period]
            for resource in model.resources
            for period in model.periods
        },
    )
    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory_per_product"]
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.terminal_inventory = pyo.Param(
        initialize=params["terminal_inventory_per_product"]
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

    def capacity_rule(instance, resource, period):
        return (
            sum(
                instance.machine_hours[resource, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.machine_capacity[resource, period]
        )

    model.capacity_constraints = pyo.Constraint(
        model.resources, model.periods, rule=capacity_rule
    )

    model.inventory_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period] <= instance.inventory_limit
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
            instance.inventory[product, 3] == instance.terminal_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
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