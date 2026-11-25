# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3]},"params":{"profit_per_unit":"P-indexed","holding_cost_per_unit":"scalar","grinder_hours_per_unit":"P-indexed","drill_hours_per_unit":"P-indexed","borer_hours_per_unit":"P-indexed","grinder_capacity":"T-indexed or scalar broadcast","drill_capacity":"T-indexed or scalar broadcast; zero in period 0","borer_capacity":"T-indexed or scalar broadcast","inventory_limit":"P-indexed or scalar broadcast","sales_limit":"T-by-P array","final_inventory":"P-indexed or scalar broadcast"},"variables":{"production[T,P]":"nonnegative continuous","sales[T,P]":"nonnegative continuous","inventory[T,P]":"nonnegative continuous"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p]","inventory[t-1,p] + production[t,p] = sales[t,p] + inventory[t,p] for t>0","sum_p grinder_hours_per_unit[p]*production[t,p] <= grinder_capacity[t]","sum_p drill_hours_per_unit[p]*production[t,p] <= (0 if t=0 else drill_capacity[t])","sum_p borer_hours_per_unit[p]*production[t,p] <= borer_capacity[t]","inventory[t,p] <= inventory_limit[p]","sales[t,p] <= sales_limit[t][p]","inventory[3,p] = final_inventory[p]"],"objective":"maximize sum_{t,p}(profit_per_unit[p]*sales[t,p] - holding_cost_per_unit*inventory[t,p])"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    def indexed_value(value, position):
        """Broadcast scalar inputs; index vector inputs."""
        if isinstance(value, Number):
            return value
        return value[position]

    profit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
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

    def balance_rule(model, period, product):
        previous_inventory = (
            0 if period == 0 else model.inventory[period - 1, product]
        )
        return (
            previous_inventory + model.production[period, product]
            == model.sales[period, product] + model.inventory[period, product]
        )

    model.balance_constraints = pyo.Constraint(
        model.periods, model.products, rule=balance_rule
    )

    def grinder_rule(model, period):
        return (
            sum(
                grinder_hours[product] * model.production[period, product]
                for product in model.products
            )
            <= indexed_value(grinder_capacity, period)
        )

    model.grinder_constraints = pyo.Constraint(
        model.periods, rule=grinder_rule
    )

    def drill_rule(model, period):
        available_capacity = (
            0 if period == 0 else indexed_value(drill_capacity, period)
        )
        return (
            sum(
                drill_hours[product] * model.production[period, product]
                for product in model.products
            )
            <= available_capacity
        )

    model.drill_constraints = pyo.Constraint(
        model.periods, rule=drill_rule
    )

    def borer_rule(model, period):
        return (
            sum(
                borer_hours[product] * model.production[period, product]
                for product in model.products
            )
            <= indexed_value(borer_capacity, period)
        )

    model.borer_constraints = pyo.Constraint(
        model.periods, rule=borer_rule
    )

    model.inventory_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda model, period, product: (
            model.inventory[period, product]
            <= indexed_value(inventory_limit, product)
        ),
    )

    model.sales_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda model, period, product: (
            model.sales[period, product] <= sales_limit[period][product]
        ),
    )

    model.final_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda model, product: (
            model.inventory[3, product]
            == indexed_value(final_inventory, product)
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit[product] * model.sales[period, product]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}