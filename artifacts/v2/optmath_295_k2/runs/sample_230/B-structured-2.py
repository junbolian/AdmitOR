# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4,5]},"params":{"profit_per_unit":"product-indexed","holding_cost_per_unit":"scalar","grinder_time":"product-indexed","drill_time":"product-indexed","borer_time":"product-indexed","grinder_capacity":"period-indexed","drill_capacity":"period-indexed","borer_capacity":"period-indexed","max_inventory":"scalar","max_sales":"product-by-period","final_inventory":"scalar or product-indexed"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p grinder_time[p]*production[p,t] <= grinder_capacity[t]","sum_p drill_time[p]*production[p,t] <= drill_capacity[t]","sum_p borer_time[p]*production[p,t] <= borer_capacity[t]","inventory[p,t] <= max_inventory","sales[p,t] <= max_sales[p,t]","inventory[p,5] = final_inventory[p], broadcasting a scalar"],"objective":"maximize sum_(p,t) profit_per_unit[p]*sales[p,t] - holding_cost_per_unit*inventory[p,t]"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 5)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda _, product: params["profit_per_unit"][product],
    )
    model.unit_holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit"]
    )

    model.grinder_hours = pyo.Param(
        model.products,
        initialize=lambda _, product: params["grinder_time"][product],
    )
    model.drill_hours = pyo.Param(
        model.products,
        initialize=lambda _, product: params["drill_time"][product],
    )
    model.borer_hours = pyo.Param(
        model.products,
        initialize=lambda _, product: params["borer_time"][product],
    )

    model.grinder_limit = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["grinder_capacity"][period],
    )
    model.drill_limit = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["drill_capacity"][period],
    )
    model.borer_limit = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["borer_capacity"][period],
    )

    model.inventory_limit = pyo.Param(initialize=params["max_inventory"])
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda _, product, period: params["max_sales"][product][period],
    )

    final_inventory = params["final_inventory"]
    model.ending_requirement = pyo.Param(
        model.products,
        initialize=lambda _, product: (
            final_inventory
            if isinstance(final_inventory, Number)
            else final_inventory[product]
        ),
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
        if period == instance.periods.first():
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
            instance.grinder_hours[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.grinder_limit[period],
    )
    model.drill_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            instance.drill_hours[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.drill_limit[period],
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            instance.borer_hours[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.borer_limit[period],
    )

    model.inventory_capacity_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period] <= instance.inventory_limit
        ),
    )
    model.sales_capacity_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period] <= instance.sales_limit[product, period]
        ),
    )
    model.final_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, instance.periods.last()]
            == instance.ending_requirement[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.unit_holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated errors; assess success below using the objective.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}