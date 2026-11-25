# IR: {"sets":{"products":[0,1,2,3],"periods":[0,1,2,3,4,5]},"params":{"profit_per_unit":"product-indexed","holding_cost":"scalar","grinding_capacity":"period-indexed","grinding_hours_per_unit":"product-indexed","drilling_capacity":"period-indexed","drilling_hours_per_unit":"product-indexed","boring_capacity":"period-indexed","boring_hours_per_unit":"product-indexed","max_inventory":"scalar","sales_limit":"product-by-period matrix","final_inventory":"scalar"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t], t>0","sum_p grinding_hours_per_unit[p]*production[p,t] <= grinding_capacity[t]","sum_p drilling_hours_per_unit[p]*production[p,t] <= drilling_capacity[t]","sum_p boring_hours_per_unit[p]*production[p,t] <= boring_capacity[t]","inventory[p,t] <= max_inventory","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = final_inventory"],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 5)

    # Mutable parameters retain symbolic expressions even for zero-valued data.
    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
        mutable=True,
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost"],
        mutable=True,
    )
    model.grinding_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["grinding_capacity"][period],
        mutable=True,
    )
    model.grinding_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["grinding_hours_per_unit"][product],
        mutable=True,
    )
    model.drilling_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["drilling_capacity"][period],
        mutable=True,
    )
    model.drilling_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["drilling_hours_per_unit"][product],
        mutable=True,
    )
    model.boring_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["boring_capacity"][period],
        mutable=True,
    )
    model.boring_hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["boring_hours_per_unit"][product],
        mutable=True,
    )
    model.max_inventory = pyo.Param(
        initialize=params["max_inventory"],
        mutable=True,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: params["sales_limit"][product][period],
        mutable=True,
    )
    model.final_inventory = pyo.Param(
        initialize=params["final_inventory"],
        mutable=True,
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

    # Tuple-form constraints avoid evaluating comparisons as Python booleans.
    def inventory_balance_rule(mdl, product, period):
        if period == 0:
            return (
                mdl.production[product, period],
                mdl.sales[product, period] + mdl.inventory[product, period],
            )
        return (
            mdl.inventory[product, period - 1] + mdl.production[product, period],
            mdl.sales[product, period] + mdl.inventory[product, period],
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.periods,
        rule=inventory_balance_rule,
    )

    model.grinding_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            None,
            sum(
                mdl.grinding_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            ),
            mdl.grinding_capacity[period],
        ),
    )
    model.drilling_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            None,
            sum(
                mdl.drilling_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            ),
            mdl.drilling_capacity[period],
        ),
    )
    model.boring_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            None,
            sum(
                mdl.boring_hours_per_unit[product]
                * mdl.production[product, period]
                for product in mdl.products
            ),
            mdl.boring_capacity[period],
        ),
    )
    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            None,
            mdl.inventory[product, period],
            mdl.max_inventory,
        ),
    )
    model.sales_ceiling = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            None,
            mdl.sales[product, period],
            mdl.sales_limit[product, period],
        ),
    )
    model.ending_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 5],
            mdl.final_inventory,
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi can raise before objective retrieval if no solution can load.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}