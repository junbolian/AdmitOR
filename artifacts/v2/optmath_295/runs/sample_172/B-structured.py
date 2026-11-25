# IR={
# "sets":{"products":[0,1,2],"periods":[0,1,2,3,4],"machines":[0,1,2]},
# "params":{"profit_per_unit":"products","holding_cost_per_unit_per_period":"scalar","machine_capacity_hours":"machines x periods","processing_time_hours":"machines x products","max_inventory_per_product":"scalar broadcast to products or products","max_sales_per_product_per_period":"products x periods","target_final_inventory":"scalar broadcast to products or products"},
# "variables":{"production":"NonNegativeReals[products,periods]","sales":"NonNegativeReals[products,periods]","inventory":"NonNegativeReals[products,periods]"},
# "constraints":[
# "initial_balance[p]: production[p,0] = sales[p,0] + inventory[p,0]",
# "inventory_balance[p,t>0]: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t]",
# "machine_capacity[k,t]: sum_p(processing_time_hours[k,p]*production[p,t]) <= machine_capacity_hours[k,t]",
# "inventory_limit[p,t]: inventory[p,t] <= max_inventory_per_product[p]",
# "sales_limit[p,t]: sales[p,t] <= max_sales_per_product_per_period[p,t]",
# "final_inventory[p]: inventory[p,4] = target_final_inventory[p]"
# ],
# "objective":"maximize sum_p,t(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t])"
# }

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _product_value(value, product):
    """Broadcast a scalar or retrieve a product-indexed value."""
    if isinstance(value, Number):
        return value
    return value[product]


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)
    model.machines = pyo.RangeSet(0, 2)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
    )
    model.machine_capacity_hours = pyo.Param(
        model.machines,
        model.periods,
        initialize=lambda mdl, machine, period: (
            params["machine_capacity_hours"][machine][period]
        ),
    )
    model.processing_time_hours = pyo.Param(
        model.machines,
        model.products,
        initialize=lambda mdl, machine, product: (
            params["processing_time_hours"][machine][product]
        ),
    )
    model.max_inventory_per_product = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _product_value(
            params["max_inventory_per_product"], product
        ),
    )
    model.max_sales_per_product_per_period = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: (
            params["max_sales_per_product_per_period"][product][period]
        ),
    )
    model.target_final_inventory = pyo.Param(
        model.products,
        initialize=lambda mdl, product: _product_value(
            params["target_final_inventory"], product
        ),
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

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(mdl, product, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.inventory[product, period - 1]
            + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.processing_time_hours[machine, product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.machine_capacity_hours[machine, period]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period]
            <= mdl.max_inventory_per_product[product]
        ),
    )

    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period]
            <= mdl.max_sales_per_product_per_period[product, period]
        ),
    )

    model.final_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 4] == mdl.target_final_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit_per_period
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}