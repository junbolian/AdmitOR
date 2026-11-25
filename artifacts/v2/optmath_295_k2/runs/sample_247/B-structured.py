# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4,5]},"params":{"profit":"P","holding_cost":"scalar","grind_capacity":"T","grind_hours":"P","drill_capacity":"scalar or T","drill_hours":"scalar or P","bore_capacity":"T, or scalar available in periods 1-5 with zero in period 0","bore_hours":"scalar or P","inv_capacity":"scalar or P","sales_limit":"P x T, product-major","final_inventory":"scalar or P"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p grind_hours[p]*production[p,t] <= grind_capacity[t]","sum_p drill_hours[p]*production[p,t] <= drill_capacity[t]","sum_p bore_hours[p]*production[p,t] <= bore_capacity[t]","inventory[p,t] <= inv_capacity[p]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = final_inventory[p]"],"objective":"maximize sum_{p,t}(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _at(data, *indices):
    """Read scalar, nested indexed, or tuple-keyed parameter data."""
    if isinstance(data, Number):
        return data
    if len(indices) > 1 and isinstance(data, Mapping) and indices in data:
        return data[indices]
    value = data
    for position in indices:
        value = value[position]
    return value


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

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(profit, product),
    )
    model.unit_holding_cost = pyo.Param(initialize=holding_cost)
    model.grinding_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: _at(grind_capacity, period),
    )
    model.grinding_requirement = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(grind_hours, product),
    )
    model.drilling_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: _at(drill_capacity, period),
    )
    model.drilling_requirement = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(drill_hours, product),
    )
    model.boring_capacity = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: (
            0
            if isinstance(bore_capacity, Number) and period == 0
            else _at(bore_capacity, period)
        ),
    )
    model.boring_requirement = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(bore_hours, product),
    )
    model.inventory_limit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(inv_capacity, product),
    )
    model.sales_upper_bound = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: _at(
            sales_limit, product, period
        ),
    )
    model.ending_inventory_requirement = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _at(final_inventory, product),
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

    def balance_rule(mdl, product, period):
        previous_inventory = (
            0 if period == 0 else mdl.inventory[product, period - 1]
        )
        return (
            previous_inventory + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )
    model.grinding_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.grinding_requirement[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.grinding_capacity[period],
    )
    model.drilling_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.drilling_requirement[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.drilling_capacity[period],
    )
    model.boring_limit = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.boring_requirement[product] * mdl.production[product, period]
            for product in mdl.products
        )
        <= mdl.boring_capacity[period],
    )
    model.inventory_capacity_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_limit[product]
        ),
    )
    model.sales_capacity_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_upper_bound[product, period]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 5]
            == mdl.ending_inventory_requirement[product]
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
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}