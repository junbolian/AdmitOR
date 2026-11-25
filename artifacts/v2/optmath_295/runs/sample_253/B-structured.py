# IR: {"sets":{"P":[0,1],"T":[0,1,2,3]},"params":{"profit_per_unit":"per product","holding_cost":"scalar or per product","grinder_hours_per_unit":"per product","drill_hours_per_unit":"per product","borer_hours_per_unit":"per product","grinder_capacity":"scalar or per period","drill_capacity":"scalar or per period","borer_capacity":"scalar or per period","inventory_limit":"scalar or per product","sales_limit":"product-by-period matrix","target_inventory":"scalar or per product"},"variables":{"production[p,t]":"continuous nonnegative","sales[p,t]":"continuous nonnegative","inventory[p,t]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in {1,2,3}","sum(grinder_hours_per_unit[p]*production[p,t] for p in P) <= grinder_capacity[t] for t in T","sum(drill_hours_per_unit[p]*production[p,t] for p in P) <= drill_capacity[t] for t in T","sum(borer_hours_per_unit[p]*production[p,t] for p in P) <= borer_capacity[t] for t in T","inventory[p,t] <= inventory_limit[p] for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = target_inventory[p] for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost[p]*inventory[p,t] for p in P, t in T); scalar parameters broadcast over their indicated index"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    def indexed_value(values, idx):
        return values if isinstance(values, Number) else values[idx]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 1)
    model.periods = pyo.RangeSet(0, 3)
    model.later_periods = pyo.RangeSet(1, 3)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(instance, product):
        return (
            instance.production[product, 0]
            == instance.sales[product, 0] + instance.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(instance, product, period):
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.later_periods, rule=inventory_balance_rule
    )

    def grinder_capacity_rule(instance, period):
        return (
            sum(
                grinder_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= indexed_value(grinder_capacity, period)
        )

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(instance, period):
        return (
            sum(
                drill_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= indexed_value(drill_capacity, period)
        )

    model.drill_capacity_constraint = pyo.Constraint(
        model.periods, rule=drill_capacity_rule
    )

    def borer_capacity_rule(instance, period):
        return (
            sum(
                borer_hours_per_unit[product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= indexed_value(borer_capacity, period)
        )

    model.borer_capacity_constraint = pyo.Constraint(
        model.periods, rule=borer_capacity_rule
    )

    def inventory_limit_rule(instance, product, period):
        return (
            instance.inventory[product, period]
            <= indexed_value(inventory_limit, product)
        )

    model.inventory_limit_constraint = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(instance, product, period):
        return instance.sales[product, period] <= sales_limit[product][period]

    model.sales_limit_constraint = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def target_inventory_rule(instance, product):
        return (
            instance.inventory[product, 3]
            == indexed_value(target_inventory, product)
        )

    model.target_inventory_constraint = pyo.Constraint(
        model.products, rule=target_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit_per_unit[product] * model.sales[product, period]
            - indexed_value(holding_cost, product)
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}