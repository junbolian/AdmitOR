# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4,5]},"params":{"profit":"P","holding_cost":"scalar","grind_capacity":"T","grind_hours":"P","drill_capacity":"T, scalar broadcast allowed","drill_hours":"P, scalar broadcast allowed","bore_capacity":"T; period 0 fixed at zero; scalar broadcast allowed","bore_hours":"P, scalar broadcast allowed","inv_capacity":"P x T, scalar broadcast allowed","sales_limit":"P x T","final_inventory":"P, scalar broadcast allowed"},"variables":{"production[P,T]":"continuous nonnegative","sales[P,T]":"continuous nonnegative","inventory[P,T]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t], t>0","sum_p grind_hours[p]*production[p,t] <= grind_capacity[t]","sum_p drill_hours[p]*production[p,t] <= drill_capacity[t]","sum_p bore_hours[p]*production[p,t] <= bore_capacity[t]","inventory[p,t] <= inv_capacity[p,t]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = final_inventory[p]"],"objective":"maximize sum_{p,t}(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _at(data, *indices):
    """Read scalar, nested indexed, or tuple-keyed indexed input."""
    if isinstance(data, Number):
        return data
    if len(indices) > 1 and isinstance(data, Mapping) and indices in data:
        return data[indices]
    result = data
    for idx in indices:
        result = result[idx]
    return result


def solve(params):
    profit = params["profit"]
    holding_cost = params["holding_cost"]
    grind_capacity = params["grind_capacity"]
    grind_hours = params["grind_hours"]
    drill_capacity = params["drill_capacity"]
    drill_hours = params["drill_hours"]
    bore_capacity = params["bore_capacity"]
    bore_hours = params["bore_hours"]
    inv_capacity = params["inv_capacity"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 5)

    model.profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(profit, product),
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        initialize=holding_cost, within=pyo.NonNegativeReals
    )
    model.grind_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: _at(grind_capacity, period),
        within=pyo.NonNegativeReals,
    )
    model.grind_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(grind_hours, product),
        within=pyo.NonNegativeReals,
    )
    model.drill_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: _at(drill_capacity, period),
        within=pyo.NonNegativeReals,
    )
    model.drill_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(drill_hours, product),
        within=pyo.NonNegativeReals,
    )
    model.bore_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: (
            0 if period == 0 else _at(bore_capacity, period)
        ),
        within=pyo.NonNegativeReals,
    )
    model.bore_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(bore_hours, product),
        within=pyo.NonNegativeReals,
    )
    model.inv_capacity = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: _at(
            inv_capacity, product, period
        ),
        within=pyo.NonNegativeReals,
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: _at(
            sales_limit, product, period
        ),
        within=pyo.NonNegativeReals,
    )
    model.final_inventory = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(final_inventory, product),
        within=pyo.NonNegativeReals,
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

    def balance_rule(mdl, product, period):
        if period == 0:
            return (
                mdl.production[product, period]
                == mdl.sales[product, period] + mdl.inventory[product, period]
            )
        return (
            mdl.inventory[product, period - 1]
            + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )
    model.grinding_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.grind_hours[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.grind_capacity[period],
    )
    model.drilling_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.drill_hours[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.drill_capacity[period],
    )
    model.boring_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.bore_hours[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.bore_capacity[period],
    )
    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inv_capacity[product, period]
        ),
    )
    model.sales_ceiling = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_limit[product, period]
        ),
    )
    model.ending_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 5] == mdl.final_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}