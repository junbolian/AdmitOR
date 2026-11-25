# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3]},"params":{"revenue":"per-product vector","holding_cost":"scalar","grinder_capacity":"scalar or per-period vector","drill_capacity":"scalar or per-period vector","borer_capacity":"scalar or per-period vector","grinder_time":"per-product vector","drill_time":"per-product vector","borer_time":"per-product vector","max_inventory":"scalar or per-product vector","sales_limits":"period-by-product matrix","target_inventory":"scalar or per-product vector"},"variables":{"production[t,p]":"nonnegative continuous","inventory[t,p]":"nonnegative continuous","sales[t,p]":"nonnegative continuous"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p] for p in P","inventory[t-1,p] + production[t,p] = sales[t,p] + inventory[t,p] for t in T excluding 0, p in P","sum(grinder_time[p]*production[t,p] for p in P) <= grinder_capacity[t] for t in T; capacity is available capacity after downtime","sum(drill_time[p]*production[t,p] for p in P) <= drill_capacity[t] for t in T; capacity is available capacity after downtime","sum(borer_time[p]*production[t,p] for p in P) <= borer_capacity[t] for t in T; capacity is available capacity after downtime","inventory[t,p] <= max_inventory[p] for t in T, p in P","sales[t,p] <= sales_limits[t][p] for t in T, p in P","inventory[3,p] = target_inventory[p] for p in P"],"objective":"maximize sum(revenue[p]*sales[t,p] - holding_cost*inventory[t,p] for t in T, p in P); scalar capacities, inventory limits, and targets are broadcast over their indices"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    max_inventory = params["max_inventory"]
    sales_limits = params["sales_limits"]
    target_inventory = params["target_inventory"]

    def indexed_value(data, idx):
        return data if isinstance(data, Number) else data[idx]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.later_periods = pyo.RangeSet(1, 3)

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[0, product]
            == mdl.sales[0, product] + mdl.inventory[0, product]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_flow_rule(mdl, period, product):
        return (
            mdl.inventory[period - 1, product] + mdl.production[period, product]
            == mdl.sales[period, product] + mdl.inventory[period, product]
        )

    model.inventory_flow = pyo.Constraint(
        model.later_periods, model.products, rule=inventory_flow_rule
    )

    def grinder_rule(mdl, period):
        return sum(
            grinder_time[product] * mdl.production[period, product]
            for product in mdl.products
        ) <= indexed_value(grinder_capacity, period)

    def drill_rule(mdl, period):
        return sum(
            drill_time[product] * mdl.production[period, product]
            for product in mdl.products
        ) <= indexed_value(drill_capacity, period)

    def borer_rule(mdl, period):
        return sum(
            borer_time[product] * mdl.production[period, product]
            for product in mdl.products
        ) <= indexed_value(borer_capacity, period)

    model.grinder_usage_limit = pyo.Constraint(model.periods, rule=grinder_rule)
    model.drill_usage_limit = pyo.Constraint(model.periods, rule=drill_rule)
    model.borer_usage_limit = pyo.Constraint(model.periods, rule=borer_rule)

    def inventory_limit_rule(mdl, period, product):
        return mdl.inventory[period, product] <= indexed_value(
            max_inventory, product
        )

    model.inventory_limit = pyo.Constraint(
        model.periods, model.products, rule=inventory_limit_rule
    )

    def sales_limit_rule(mdl, period, product):
        return mdl.sales[period, product] <= sales_limits[period][product]

    model.sales_limit = pyo.Constraint(
        model.periods, model.products, rule=sales_limit_rule
    )

    def terminal_inventory_rule(mdl, product):
        return mdl.inventory[3, product] == indexed_value(
            target_inventory, product
        )

    model.terminal_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            revenue[product] * model.sales[period, product]
            - holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}