# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4]},"params":{"profit_per_unit":"real[products]","holding_cost_per_unit_per_period":"real scalar","grinder_hours":"real[periods]","drill_hours":"real[periods]","borer_hours":"real[periods]","machine_time_grinder":"real[products]","machine_time_drill":"real[products]","machine_time_borer":"real[products]","inventory_capacity":"real scalar","sales_limit":"real[products,periods]","target_final_inventory":"real[products]"},"variables":{"production":"continuous nonnegative[products,periods]","inventory":"continuous nonnegative[products,periods]","sales":"continuous nonnegative[products,periods]"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum_p(machine_time_grinder[p]*production[p,t]) <= grinder_hours[t] for each period t","sum_p(machine_time_drill[p]*production[p,t]) <= drill_hours[t] for each period t","sum_p(machine_time_borer[p]*production[p,t]) <= borer_hours[t] for each period t","inventory[p,t] <= inventory_capacity for each product p and period t","sales[p,t] <= sales_limit[p,t] for each product p and period t","inventory[p,4] = target_final_inventory[p] for each product p"],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
        within=pyo.Reals,
    )

    model.grinder_hours = pyo.Param(
        model.periods,
        initialize={
            period: params["grinder_hours"][period]
            for period in model.periods
        },
        within=pyo.Reals,
    )
    model.drill_hours = pyo.Param(
        model.periods,
        initialize={
            period: params["drill_hours"][period]
            for period in model.periods
        },
        within=pyo.Reals,
    )
    model.borer_hours = pyo.Param(
        model.periods,
        initialize={
            period: params["borer_hours"][period]
            for period in model.periods
        },
        within=pyo.Reals,
    )

    model.machine_time_grinder = pyo.Param(
        model.products,
        initialize={
            product: params["machine_time_grinder"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.machine_time_drill = pyo.Param(
        model.products,
        initialize={
            product: params["machine_time_drill"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.machine_time_borer = pyo.Param(
        model.products,
        initialize={
            product: params["machine_time_borer"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"],
        within=pyo.Reals,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): params["sales_limit"][product][period]
            for product in model.products
            for period in model.periods
        },
        within=pyo.Reals,
    )
    model.target_final_inventory = pyo.Param(
        model.products,
        initialize={
            product: params["target_final_inventory"][product]
            for product in model.products
        },
        within=pyo.Reals,
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

    def grinder_capacity_rule(factory, period):
        return (
            sum(
                factory.machine_time_grinder[product]
                * factory.production[product, period]
                for product in factory.products
            )
            <= factory.grinder_hours[period]
        )

    model.grinder_capacity = pyo.Constraint(
        model.periods, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(factory, period):
        return (
            sum(
                factory.machine_time_drill[product]
                * factory.production[product, period]
                for product in factory.products
            )
            <= factory.drill_hours[period]
        )

    model.drill_capacity = pyo.Constraint(
        model.periods, rule=drill_capacity_rule
    )

    def borer_capacity_rule(factory, period):
        return (
            sum(
                factory.machine_time_borer[product]
                * factory.production[product, period]
                for product in factory.products
            )
            <= factory.borer_hours[period]
        )

    model.borer_capacity = pyo.Constraint(
        model.periods, rule=borer_capacity_rule
    )

    def inventory_limit_rule(factory, product, period):
        return (
            factory.inventory[product, period]
            <= factory.inventory_capacity
        )

    model.inventory_limits = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(factory, product, period):
        return (
            factory.sales[product, period]
            <= factory.sales_limit[product, period]
        )

    model.sales_limits = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def final_inventory_rule(factory, product):
        return (
            factory.inventory[product, 4]
            == factory.target_final_inventory[product]
        )

    model.final_inventory_requirement = pyo.Constraint(
        model.products, rule=final_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit_per_period
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}