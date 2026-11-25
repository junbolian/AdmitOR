# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3],"T_later":[1,2,3]},
# "params":{"profit_per_unit":"P","holding_cost_per_unit_per_period":"scalar","machine_hours_grinder":"P","machine_hours_drill":"P","machine_hours_borer":"P","grinder_capacity":"T","drill_capacity":"T","borer_capacity":"T","inventory_limit":"scalar","sales_limit":"T x P","target_inventory":"scalar broadcast to P, or indexed by P"},
# "variables":{"production[T,P]":"nonnegative continuous","inventory[T,P]":"nonnegative continuous","sales[T,P]":"nonnegative continuous"},
# "constraints":["initial_balance[p]: production[0,p] = sales[0,p] + inventory[0,p]","inventory_balance[t,p], t in T_later: production[t,p] + inventory[t-1,p] = sales[t,p] + inventory[t,p]","grinder_capacity[t]: sum_p machine_hours_grinder[p]*production[t,p] <= grinder_capacity[t]","drill_capacity[t]: sum_p machine_hours_drill[p]*production[t,p] <= drill_capacity[t]","borer_capacity[t]: sum_p machine_hours_borer[p]*production[t,p] <= borer_capacity[t]","inventory_limit[t,p]: inventory[t,p] <= inventory_limit","sales_limit[t,p]: sales[t,p] <= sales_limit[t,p]","ending_inventory[p]: inventory[3,p] = target_inventory[p]"],
# "objective":"maximize sum_(t,p) (profit_per_unit[p]*sales[t,p] - holding_cost_per_unit_per_period*inventory[t,p])"}

from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.later_periods = pyo.RangeSet(1, 3)

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"]
    )

    model.grinder_hours = pyo.Param(
        model.products,
        initialize={
            product: params["machine_hours_grinder"][product]
            for product in model.products
        },
    )
    model.drill_hours = pyo.Param(
        model.products,
        initialize={
            product: params["machine_hours_drill"][product]
            for product in model.products
        },
    )
    model.borer_hours = pyo.Param(
        model.products,
        initialize={
            product: params["machine_hours_borer"][product]
            for product in model.products
        },
    )

    model.grinder_available = pyo.Param(
        model.periods,
        initialize={
            period: params["grinder_capacity"][period]
            for period in model.periods
        },
    )
    model.drill_available = pyo.Param(
        model.periods,
        initialize={
            period: params["drill_capacity"][period]
            for period in model.periods
        },
    )
    model.borer_available = pyo.Param(
        model.periods,
        initialize={
            period: params["borer_capacity"][period]
            for period in model.periods
        },
    )

    model.inventory_ceiling = pyo.Param(
        initialize=params["inventory_limit"]
    )
    model.sales_ceiling = pyo.Param(
        model.periods,
        model.products,
        initialize={
            (period, product): params["sales_limit"][period][product]
            for period in model.periods
            for product in model.products
        },
    )

    target_data = params["target_inventory"]
    model.ending_target = pyo.Param(
        model.products,
        initialize={
            product: (
                target_data
                if isinstance(target_data, Real)
                else target_data[product]
            )
            for product in model.products
        },
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

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[0, product]
            == mdl.sales[0, product] + mdl.inventory[0, product]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(mdl, period, product):
        return (
            mdl.production[period, product]
            + mdl.inventory[period - 1, product]
            == mdl.sales[period, product] + mdl.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.later_periods,
        model.products,
        rule=inventory_balance_rule,
    )

    def grinder_capacity_rule(mdl, period):
        return (
            sum(
                mdl.grinder_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.grinder_available[period]
        )

    model.grinder_capacity_constraint = pyo.Constraint(
        model.periods, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(mdl, period):
        return (
            sum(
                mdl.drill_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.drill_available[period]
        )

    model.drill_capacity_constraint = pyo.Constraint(
        model.periods, rule=drill_capacity_rule
    )

    def borer_capacity_rule(mdl, period):
        return (
            sum(
                mdl.borer_hours[product] * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.borer_available[period]
        )

    model.borer_capacity_constraint = pyo.Constraint(
        model.periods, rule=borer_capacity_rule
    )

    model.inventory_limit_constraint = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.inventory[period, product] <= mdl.inventory_ceiling
        ),
    )

    model.sales_limit_constraint = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.sales[period, product] <= mdl.sales_ceiling[period, product]
        ),
    )

    model.ending_inventory_constraint = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}