# IR: {"sets":{"T":[0,1,2,3],"P":[0,1,2],"K":[0,1,2]},"params":{"profit_per_unit":"P-indexed","holding_cost":"scalar","machine_hours_per_unit":"P-by-K; K=grinder,drill,borer","grinder_capacity":"T-indexed","drill_capacity":"T-indexed","borer_capacity":"T-indexed","inventory_capacity":"scalar or P-indexed","sales_limit":"T-by-P","target_inventory":"scalar or P-indexed"},"variables":{"production[T,P]":"nonnegative continuous","inventory[T,P]":"nonnegative continuous","sales[T,P]":"nonnegative continuous"},"constraints":["production[0,p]=sales[0,p]+inventory[0,p] for p in P","production[t,p]+inventory[t-1,p]=sales[t,p]+inventory[t,p] for t in T excluding 0,p in P","sum(machine_hours_per_unit[p,k]*production[t,p] for p in P)<=machine_capacity[k,t] for k in K,t in T; machine_capacity comes from grinder_capacity,drill_capacity,borer_capacity","inventory[t,p]<=inventory_capacity[p] for t in T,p in P; broadcast scalar capacity","sales[t,p]<=sales_limit[t,p] for t in T,p in P","inventory[3,p]=target_inventory[p] for p in P; broadcast scalar target"],"objective":"maximize sum(profit_per_unit[p]*sales[t,p]-holding_cost*inventory[t,p] for t in T,p in P)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous production, inventory, and sales planning model."""

    profit_data = params["profit_per_unit"]
    holding_data = params["holding_cost"]
    hours_data = params["machine_hours_per_unit"]
    grinder_data = params["grinder_capacity"]
    drill_data = params["drill_capacity"]
    borer_data = params["borer_capacity"]
    inventory_data = params["inventory_capacity"]
    sales_data = params["sales_limit"]
    target_data = params["target_inventory"]

    def product_value(data, product):
        return data if isinstance(data, Number) else data[product]

    capacity_data = (grinder_data, drill_data, borer_data)

    model = pyo.ConcreteModel()

    model.periods = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)
    model.machine_types = pyo.RangeSet(0, 2)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profit_data[product],
    )
    model.unit_holding_cost = pyo.Param(initialize=holding_data)
    model.machine_hours = pyo.Param(
        model.products,
        model.machine_types,
        initialize=lambda mdl, product, machine: hours_data[product][machine],
    )
    model.machine_capacity = pyo.Param(
        model.machine_types,
        model.periods,
        initialize=lambda mdl, machine, period: capacity_data[machine][period],
    )
    model.inventory_limit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: product_value(inventory_data, product),
    )
    model.sales_limit = pyo.Param(
        model.periods,
        model.products,
        initialize=lambda mdl, period, product: sales_data[period][product],
    )
    model.final_inventory_target = pyo.Param(
        model.products,
        initialize=lambda mdl, product: product_value(target_data, product),
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
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.production[period, product] + mdl.inventory[period - 1, product]
            == mdl.sales[period, product] + mdl.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, model.products, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.machine_hours[product, machine]
                * mdl.production[period, product]
                for product in mdl.products
            )
            <= mdl.machine_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machine_types, model.periods, rule=machine_capacity_rule
    )

    model.inventory_capacity_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.inventory[period, product] <= mdl.inventory_limit[product]
        ),
    )

    model.sales_limit_constraints = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda mdl, period, product: (
            mdl.sales[period, product] <= mdl.sales_limit[period, product]
        ),
    )

    model.final_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[3, product] == mdl.final_inventory_target[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[period, product]
            - model.unit_holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}