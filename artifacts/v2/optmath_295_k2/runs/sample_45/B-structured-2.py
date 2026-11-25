# IR: {"sets":{"T":[0,1,2,3],"P":[0,1,2]},"params":{"profit_per_unit":"P","holding_cost_per_unit_per_period":"scalar","machine_hours_grinder":"P","machine_hours_drill":"P","machine_hours_borer":"P","grinder_capacity":"T","drill_capacity":"T","borer_capacity":"T","inventory_limit":"scalar","sales_limit":"T x P","target_inventory":"scalar broadcast to P, or P-indexed"},"variables":{"production[T,P]":"nonnegative continuous","inventory[T,P]":"nonnegative continuous","sales[T,P]":"nonnegative continuous"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p] for p in P","production[t,p] + inventory[t-1,p] = sales[t,p] + inventory[t,p] for t in T excluding 0, p in P","sum(machine_hours_grinder[p]*production[t,p] for p in P) <= grinder_capacity[t] for t in T","sum(machine_hours_drill[p]*production[t,p] for p in P) <= drill_capacity[t] for t in T","sum(machine_hours_borer[p]*production[t,p] for p in P) <= borer_capacity[t] for t in T","inventory[t,p] <= inventory_limit for t in T, p in P","sales[t,p] <= sales_limit[t,p] for t in T, p in P","inventory[3,p] = target_inventory[p] for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[t,p] - holding_cost_per_unit_per_period*inventory[t,p] for t in T, p in P)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.periods = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)
    model.later_periods = pyo.RangeSet(1, 3)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
    )
    model.grinder_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["machine_hours_grinder"][product],
    )
    model.drill_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["machine_hours_drill"][product],
    )
    model.borer_hours = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["machine_hours_borer"][product],
    )
    model.grinder_available = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["grinder_capacity"][period],
    )
    model.drill_available = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["drill_capacity"][period],
    )
    model.borer_available = pyo.Param(
        model.periods,
        initialize=lambda mdl, period: params["borer_capacity"][period],
    )
    model.inventory_cap = pyo.Param(
        initialize=params["inventory_limit"],
    )
    model.sales_cap = pyo.Param(
        model.periods,
        model.products,
        initialize=lambda mdl, period, product: params["sales_limit"][period][product],
    )

    target_inventory = params["target_inventory"]
    model.ending_target = pyo.Param(
        model.products,
        initialize=lambda mdl, product: (
            target_inventory
            if isinstance(target_inventory, Number)
            else target_inventory[product]
        ),
    )

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    model.initial_balance = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[0, product]
            == mdl.sales[0, product] + mdl.inventory[0, product]
        ),
    )
    model.inventory_balance = pyo.Constraint(
        model.later_periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.production[period, product] + mdl.inventory[period - 1, product]
            == mdl.sales[period, product] + mdl.inventory[period, product]
        ),
    )
    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.grinder_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.grinder_available[period]
        ),
    )
    model.drill_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.drill_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.drill_available[period]
        ),
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.borer_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.borer_available[period]
        ),
    )
    model.inventory_limit_constraint = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.inventory[period, product] <= mdl.inventory_cap
        ),
    )
    model.sales_limit_constraint = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.sales[period, product] <= mdl.sales_cap[period, product]
        ),
    )
    model.target_inventory_constraint = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[3, product] == mdl.ending_target[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[period, product]
            - model.holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Still determine success solely by objective-value retrieval below.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}