# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"profit_per_unit":"P","holding_cost_per_unit":"scalar","grinder_time":"P","drill_time":"P","borer_time":"P","grinder_capacity":"T","drill_capacity":"T","borer_capacity":"T","max_inventory":"scalar or P-indexed","max_sales":"P x T","final_inventory":"scalar or P-indexed"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t], t>0","sum_p grinder_time[p]*production[p,t] <= grinder_capacity[t]","sum_p drill_time[p]*production[p,t] <= drill_capacity[t]","sum_p borer_time[p]*production[p,t] <= borer_capacity[t]","inventory[p,t] <= max_inventory[p]","sales[p,t] <= max_sales[p,t]","inventory[p,5] = final_inventory[p]"],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit*inventory[p,t])"}
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 5)

    def product_value(value, product):
        return value if isinstance(value, Number) else value[product]

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda _, product: params["profit_per_unit"][product],
    )
    model.holding_cost_per_unit = pyo.Param(
        initialize=params["holding_cost_per_unit"]
    )

    model.grinder_time = pyo.Param(
        model.products,
        initialize=lambda _, product: params["grinder_time"][product],
    )
    model.drill_time = pyo.Param(
        model.products,
        initialize=lambda _, product: params["drill_time"][product],
    )
    model.borer_time = pyo.Param(
        model.products,
        initialize=lambda _, product: params["borer_time"][product],
    )

    model.grinder_capacity = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["grinder_capacity"][period],
    )
    model.drill_capacity = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["drill_capacity"][period],
    )
    model.borer_capacity = pyo.Param(
        model.periods,
        initialize=lambda _, period: params["borer_capacity"][period],
    )

    model.max_inventory = pyo.Param(
        model.products,
        initialize=lambda _, product: product_value(
            params["max_inventory"], product
        ),
    )
    model.max_sales = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda _, product, period: params["max_sales"][product][period],
    )
    model.final_inventory = pyo.Param(
        model.products,
        initialize=lambda _, product: product_value(
            params["final_inventory"], product
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

    model.grinder_limit = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            instance.grinder_time[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.grinder_capacity[period],
    )
    model.drill_limit = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            instance.drill_time[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.drill_capacity[period],
    )
    model.borer_limit = pyo.Constraint(
        model.periods,
        rule=lambda instance, period: sum(
            instance.borer_time[product] * instance.production[product, period]
            for product in instance.products
        )
        <= instance.borer_capacity[period],
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= instance.max_inventory[product]
        ),
    )
    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.max_sales[product, period]
        ),
    )
    model.ending_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 5] == instance.final_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit * model.inventory[product, period]
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