# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4,5]},"params":{"profit":"P","holding_cost":"scalar","grinder_capacity":"scalar or T","drill_capacity":"scalar or T","borer_capacity":"scalar or T; unavailable at t=3","grinder_time":"P","drill_time":"P","borer_time":"P","inventory_limit":"scalar or P","sales_limit":"P x T","target_inventory":"scalar or P"},"variables":{"production[P,T]":"continuous >= 0","inventory[P,T]":"continuous >= 0","sales[P,T]":"continuous >= 0"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p grinder_time[p]*production[p,t] <= grinder_capacity[t]","sum_p drill_time[p]*production[p,t] <= drill_capacity[t]","sum_p borer_time[p]*production[p,t] <= borer_capacity[t]*I(t!=3)","inventory[p,t] <= inventory_limit[p]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = target_inventory[p]"],"objective":"maximize sum_(p,t)(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position, label):
    """Read a sequence or a mapping keyed by label, integer, or integer string."""
    if isinstance(data, Mapping):
        for key in (label, position, str(position)):
            if key in data:
                return data[key]
        raise KeyError(label)
    return data[position]


def _product_value(data, product):
    return _indexed_value(data, product, f"product_{product}")


def _period_value(data, period):
    return _indexed_value(data, period, f"period_{period}")


def _scalar_or_product(data, product):
    if isinstance(data, Number):
        return data
    return _product_value(data, product)


def _scalar_or_period(data, period):
    if isinstance(data, Number):
        return data
    return _period_value(data, period)


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 5)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda _, product: _product_value(
            params["profit"], product
        ),
    )
    model.inventory_cost = pyo.Param(initialize=params["holding_cost"])

    model.grinder_hours = pyo.Param(
        model.periods,
        initialize=lambda _, period: _scalar_or_period(
            params["grinder_capacity"], period
        ),
    )
    model.drill_hours = pyo.Param(
        model.periods,
        initialize=lambda _, period: _scalar_or_period(
            params["drill_capacity"], period
        ),
    )
    model.borer_hours = pyo.Param(
        model.periods,
        initialize=lambda _, period: _scalar_or_period(
            params["borer_capacity"], period
        ),
    )

    model.grinder_requirement = pyo.Param(
        model.products,
        initialize=lambda _, product: _product_value(
            params["grinder_time"], product
        ),
    )
    model.drill_requirement = pyo.Param(
        model.products,
        initialize=lambda _, product: _product_value(
            params["drill_time"], product
        ),
    )
    model.borer_requirement = pyo.Param(
        model.products,
        initialize=lambda _, product: _product_value(
            params["borer_time"], product
        ),
    )

    model.inventory_ceiling = pyo.Param(
        model.products,
        initialize=lambda _, product: _scalar_or_product(
            params["inventory_limit"], product
        ),
    )
    model.sales_ceiling = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda _, product, period: _period_value(
            _product_value(params["sales_limit"], product), period
        ),
    )
    model.ending_requirement = pyo.Param(
        model.products,
        initialize=lambda _, product: _scalar_or_product(
            params["target_inventory"], product
        ),
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

    def inventory_balance_rule(_, product, period):
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

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda _, period: sum(
            model.grinder_requirement[product]
            * model.production[product, period]
            for product in model.products
        )
        <= model.grinder_hours[period],
    )
    model.drill_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda _, period: sum(
            model.drill_requirement[product]
            * model.production[product, period]
            for product in model.products
        )
        <= model.drill_hours[period],
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda _, period: sum(
            model.borer_requirement[product]
            * model.production[product, period]
            for product in model.products
        )
        <= model.borer_hours[period] * int(period != 3),
    )

    model.inventory_limit_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda _, product, period: (
            model.inventory[product, period]
            <= model.inventory_ceiling[product]
        ),
    )
    model.sales_limit_constraint = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda _, product, period: (
            model.sales[product, period] <= model.sales_ceiling[product, period]
        ),
    )
    model.target_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda _, product: (
            model.inventory[product, 5] == model.ending_requirement[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.inventory_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    # APPsi HiGHS raises RuntimeError when it cannot load a solution.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    # Objective retrieval is the sole success test.
    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}