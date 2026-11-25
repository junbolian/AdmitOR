# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3]},"params":["profit_p0","profit_p1","holding_cost","grinder_hours_per_unit","drill_hours_per_unit","borer_hours_per_unit_p0","borer_hours_per_unit_p1","grinder_capacity","drill_capacity","borer_capacity","inventory_limit","sales_limit_p0","sales_limit_p1","target_inventory"],"decisions":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and t=1,2,3","grinder_hours_per_unit * sum_p production[p,t] <= grinder_capacity for each period t","drill_hours_per_unit * sum_p production[p,t] <= drill_capacity for each period t","borer_hours_per_unit_p0 * production[0,t] + borer_hours_per_unit_p1 * production[1,t] <= borer_capacity for each period t","inventory[p,t] <= inventory_limit for each product p and period t","sales[p,t] <= sales_limit_p{p}[t] for each product p and period t","inventory[p,3] = target_inventory for each product p"],"objective":"maximize sum_{p,t}(profit_p{p} * sales[p,t] - holding_cost * inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Sales-limit parameters must be sequences or mappings indexed by period."""
    profit = {
        0: params["profit_p0"],
        1: params["profit_p1"],
    }
    holding_cost = params["holding_cost"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = {
        0: params["borer_hours_per_unit_p0"],
        1: params["borer_hours_per_unit_p1"],
    }
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limits = {
        0: params["sales_limit_p0"],
        1: params["sales_limit_p1"],
    }
    target_inventory = params["target_inventory"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def balance_rule(block, product, period):
        if period == 0:
            return (
                block.production[product, period]
                == block.sales[product, period] + block.inventory[product, period]
            )
        return (
            block.inventory[product, period - 1]
            + block.production[product, period]
            == block.sales[product, period] + block.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def grinding_rule(block, period):
        return (
            grinder_hours
            * sum(block.production[product, period] for product in block.products)
            <= grinder_capacity
        )

    model.grinding_capacity_constraint = pyo.Constraint(
        model.periods, rule=grinding_rule
    )

    def drilling_rule(block, period):
        return (
            drill_hours
            * sum(block.production[product, period] for product in block.products)
            <= drill_capacity
        )

    model.drilling_capacity_constraint = pyo.Constraint(
        model.periods, rule=drilling_rule
    )

    def boring_rule(block, period):
        return (
            sum(
                borer_hours[product] * block.production[product, period]
                for product in block.products
            )
            <= borer_capacity
        )

    model.boring_capacity_constraint = pyo.Constraint(
        model.periods, rule=boring_rule
    )

    model.inventory_limit_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.inventory[product, period] <= inventory_limit
        ),
    )

    model.sales_limit_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.sales[product, period] <= sales_limits[product][period]
        ),
    )

    model.target_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda block, product: (
            block.inventory[product, 3] == target_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit[product] * model.sales[product, period]
            - holding_cost * model.inventory[product, period]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}