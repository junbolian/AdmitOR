# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"profit_per_unit":"P-vector","holding_cost_per_unit_per_period":"scalar","grinder_hours_per_unit":"P-vector","drill_hours_per_unit":"P-vector","borer_hours_per_unit":"P-vector","grinder_capacity_per_period":"T-vector","drill_capacity_per_period":"T-vector","borer_capacity_per_period":"T-vector","max_inventory_per_product":"scalar or P-vector","max_sales":"P-by-T matrix","final_inventory_target":"scalar or P-vector"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T excluding 0","sum_p grinder_hours_per_unit[p]*production[p,t] <= grinder_capacity_per_period[t] for t in T","sum_p drill_hours_per_unit[p]*production[p,t] <= drill_capacity_per_period[t] for t in T","sum_p borer_hours_per_unit[p]*production[p,t] <= borer_capacity_per_period[t] for t in T","inventory[p,t] <= max_inventory_per_product[p] for p in P, t in T (broadcast scalar)","sales[p,t] <= max_sales[p][t] for p in P, t in T","inventory[p,5] = final_inventory_target[p] for p in P (broadcast scalar)"],"objective":"maximize sum_(p,t) profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t]"}
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    grinder_capacity = params["grinder_capacity_per_period"]
    drill_capacity = params["drill_capacity_per_period"]
    borer_capacity = params["borer_capacity_per_period"]
    inventory_limit = params["max_inventory_per_product"]
    sales_limit = params["max_sales"]
    final_target = params["final_inventory_target"]

    def product_value(data, product):
        return data if isinstance(data, Number) else data[product]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 5)

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

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            grinder_hours[product] * instance.production[product, period]
            for product in instance.products
        ) <= grinder_capacity[period],
    )
    model.drill_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            drill_hours[product] * instance.production[product, period]
            for product in instance.products
        ) <= drill_capacity[period],
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            borer_hours[product] * instance.production[product, period]
            for product in instance.products
        ) <= borer_capacity[period],
    )
    model.inventory_capacity_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= product_value(inventory_limit, product)
        ),
    )
    model.sales_limit_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period] <= sales_limit[product][period]
        ),
    )
    model.final_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 5]
            == product_value(final_target, product)
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
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}