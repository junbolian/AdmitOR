# IR: {"sets":{"T":[0,1,2,3],"P":[0,1,2]},"params":{"profit_per_unit":"P-indexed","holding_cost":"scalar","grinder_capacity":"scalar or T-indexed","drill_capacity":"scalar or T-indexed; unavailable at t=0","borer_capacity":"scalar or T-indexed; unavailable at t=1","grinder_time":"P-indexed","drill_time":"P-indexed","borer_time":"P-indexed","max_inventory":"scalar","max_sales":"T-by-P indexed","final_inventory":"scalar or P-indexed"},"variables":{"production[t,p]":"nonnegative continuous","sales[t,p]":"nonnegative continuous","inventory[t,p]":"nonnegative continuous"},"constraints":["production[0,p]=sales[0,p]+inventory[0,p]","inventory[t-1,p]+production[t,p]=sales[t,p]+inventory[t,p] for t>0","sum_p grinder_time[p]*production[t,p]<=grinder_capacity[t]","sum_p drill_time[p]*production[t,p]<=0 if t=0 else drill_capacity[t]","sum_p borer_time[p]*production[t,p]<=0 if t=1 else borer_capacity[t]","inventory[t,p]<=max_inventory","sales[t,p]<=max_sales[t,p]","inventory[3,p]=final_inventory[p]"],"objective":"maximize sum_(t,p) profit_per_unit[p]*sales[t,p]-holding_cost*inventory[t,p]"}
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_or_scalar(value, position):
    """Accept either a numeric scalar or an indexable sequence/mapping."""
    if isinstance(value, Number):
        return value
    return value[position]


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    def balance_rule(block, period, product):
        if period == 0:
            return (
                block.production[period, product]
                == block.sales[period, product]
                + block.inventory[period, product]
            )
        return (
            block.inventory[period - 1, product]
            + block.production[period, product]
            == block.sales[period, product]
            + block.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, model.products, rule=balance_rule
    )

    def grinder_rule(block, period):
        return (
            sum(
                grinder_time[product] * block.production[period, product]
                for product in block.products
            )
            <= _indexed_or_scalar(grinder_capacity, period)
        )

    model.grinder_limit = pyo.Constraint(model.periods, rule=grinder_rule)

    def drill_rule(block, period):
        available_hours = (
            0 if period == 0 else _indexed_or_scalar(drill_capacity, period)
        )
        return (
            sum(
                drill_time[product] * block.production[period, product]
                for product in block.products
            )
            <= available_hours
        )

    model.drill_limit = pyo.Constraint(model.periods, rule=drill_rule)

    def borer_rule(block, period):
        available_hours = (
            0 if period == 1 else _indexed_or_scalar(borer_capacity, period)
        )
        return (
            sum(
                borer_time[product] * block.production[period, product]
                for product in block.products
            )
            <= available_hours
        )

    model.borer_limit = pyo.Constraint(model.periods, rule=borer_rule)

    model.inventory_limit = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda block, period, product: (
            block.inventory[period, product] <= max_inventory
        ),
    )

    model.sales_limit = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda block, period, product: (
            block.sales[period, product] <= max_sales[period][product]
        ),
    )

    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda block, product: (
            block.inventory[3, product]
            == _indexed_or_scalar(final_inventory, product)
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit_per_unit[product] * model.sales[period, product]
            - holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}