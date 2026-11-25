# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3]},"params":["profit_per_unit_p0","profit_per_unit_p1","holding_cost_per_unit_per_period","grinder_capacity_period","drill_capacity_period","borer_capacity_period","grinder_hours_per_unit_p0","grinder_hours_per_unit_p1","drill_hours_per_unit","borer_hours_per_unit","max_inventory_per_product_per_period","max_sales_p0_period","max_sales_p1_period","final_inventory_p0","final_inventory_p1"],"variables":{"production[p,t]":"continuous nonnegative","sales[p,t]":"continuous nonnegative","inventory[p,t]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t > 0","sum(p, grinder_hours[p] * production[p,t]) <= grinder_capacity[t]","drill_hours * sum(p, production[p,t]) <= drill_capacity[t]","borer_hours * sum(p, production[p,t]) <= borer_capacity[t]","inventory[p,t] <= max_inventory","sales[p,t] <= max_sales[p,t]","inventory[p,3] = final_inventory[p]"],"objective":"maximize sum(p,t, profit[p] * sales[p,t] - holding_cost * inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)

    profit = {
        0: params["profit_per_unit_p0"],
        1: params["profit_per_unit_p1"],
    }
    grinder_hours = {
        0: params["grinder_hours_per_unit_p0"],
        1: params["grinder_hours_per_unit_p1"],
    }
    sales_limits = {
        0: params["max_sales_p0_period"],
        1: params["max_sales_p1_period"],
    }
    ending_inventory = {
        0: params["final_inventory_p0"],
        1: params["final_inventory_p1"],
    }

    model.unit_profit = pyo.Param(model.products, initialize=profit)
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"]
    )
    model.grinder_capacity = pyo.Param(
        model.periods,
        initialize={
            period: params["grinder_capacity_period"][period]
            for period in model.periods
        },
    )
    model.drill_capacity = pyo.Param(
        model.periods,
        initialize={
            period: params["drill_capacity_period"][period]
            for period in model.periods
        },
    )
    model.borer_capacity = pyo.Param(
        model.periods,
        initialize={
            period: params["borer_capacity_period"][period]
            for period in model.periods
        },
    )
    model.grinder_hours = pyo.Param(model.products, initialize=grinder_hours)
    model.drill_hours = pyo.Param(initialize=params["drill_hours_per_unit"])
    model.borer_hours = pyo.Param(initialize=params["borer_hours_per_unit"])
    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory_per_product_per_period"]
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
    model.ending_inventory = pyo.Param(
        model.products, initialize=ending_inventory
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

    def grinder_capacity_rule(model, period):
        return (
            sum(
                model.grinder_hours[product] * model.production[product, period]
                for product in model.products
            )
            <= model.grinder_capacity[period]
        )

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(model, period):
        return (
            model.drill_hours
            * sum(
                model.production[product, period]
                for product in model.products
            )
            <= model.drill_capacity[period]
        )

    model.drill_capacity_constraint = pyo.Constraint(
        model.periods, rule=drill_capacity_rule
    )

    def borer_capacity_rule(model, period):
        return (
            model.borer_hours
            * sum(
                model.production[product, period]
                for product in model.products
            )
            <= model.borer_capacity[period]
        )

    model.borer_capacity_constraint = pyo.Constraint(
        model.periods, rule=borer_capacity_rule
    )

    def inventory_limit_rule(model, product, period):
        return model.inventory[product, period] <= model.inventory_limit

    model.inventory_limit_constraint = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(model, product, period):
        return model.sales[product, period] <= model.sales_limit[product, period]

    model.sales_limit_constraint = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def final_inventory_rule(model, product):
        return model.inventory[product, 3] == model.ending_inventory[product]

    model.final_inventory_constraint = pyo.Constraint(
        model.products, rule=final_inventory_rule
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}