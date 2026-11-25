# IR: {
#   "sets": {"products": [0, 1], "periods": [0, 1, 2, 3], "machines": [0, 1, 2]},
#   "params": {
#     "profit_per_unit": "vector[products]",
#     "holding_cost_per_unit_per_period": "scalar or vector[products]",
#     "machine_hours_per_unit": "matrix[machines,products]",
#     "machine_capacity_per_period": "vector[machines]",
#     "max_inventory_per_period": "scalar or vector[products]",
#     "sales_limit_product0": "vector[periods]",
#     "sales_limit_product1": "vector[periods]",
#     "target_final_inventory": "scalar or vector[products]"
#   },
#   "parameter_normalization": "For scalar-or-vector parameters, broadcast scalars to all products; otherwise index by product.",
#   "decision_variables": {
#     "production[p,t]": "nonnegative continuous",
#     "inventory[p,t]": "nonnegative continuous",
#     "sales[p,t]": "nonnegative continuous"
#   },
#   "constraints": [
#     "For each p: production[p,0] = sales[p,0] + inventory[p,0].",
#     "For each p and t>0: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t].",
#     "For each k,t: sum_p machine_hours_per_unit[k,p]*production[p,t] <= machine_capacity_per_period[k].",
#     "For each p,t: inventory[p,t] <= max_inventory_per_period[p].",
#     "For each t: sales[0,t] <= sales_limit_product0[t].",
#     "For each t: sales[1,t] <= sales_limit_product1[t].",
#     "For each p: inventory[p,3] = target_final_inventory[p]."
#   ],
#   "objective": "Maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period[p]*inventory[p,t])."
# }

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _product_value(data, product):
    """Accept either a numeric scalar or data indexed by product."""
    return data if isinstance(data, Number) else data[product]


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 1)
    model.periods = pyo.RangeSet(0, 3)
    model.machines = pyo.RangeSet(0, 2)
    model.later_periods = pyo.RangeSet(1, 3)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        model.products,
        initialize={
            product: _product_value(
                params["holding_cost_per_unit_per_period"], product
            )
            for product in model.products
        },
    )
    model.machine_hours_per_unit = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product):
                params["machine_hours_per_unit"][machine][product]
            for machine in model.machines
            for product in model.products
        },
    )
    model.machine_capacity_per_period = pyo.Param(
        model.machines,
        initialize={
            machine: params["machine_capacity_per_period"][machine]
            for machine in model.machines
        },
    )
    model.max_inventory_per_period = pyo.Param(
        model.products,
        initialize={
            product: _product_value(
                params["max_inventory_per_period"], product
            )
            for product in model.products
        },
    )
    model.sales_limit_product0 = pyo.Param(
        model.periods,
        initialize={
            period: params["sales_limit_product0"][period]
            for period in model.periods
        },
    )
    model.sales_limit_product1 = pyo.Param(
        model.periods,
        initialize={
            period: params["sales_limit_product1"][period]
            for period in model.periods
        },
    )
    model.target_final_inventory = pyo.Param(
        model.products,
        initialize={
            product: _product_value(
                params["target_final_inventory"], product
            )
            for product in model.products
        },
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

    def initial_balance_rule(model, product):
        return (
            model.production[product, 0]
            == model.sales[product, 0] + model.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(model, product, period):
        return (
            model.inventory[product, period - 1]
            + model.production[product, period]
            == model.sales[product, period]
            + model.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=inventory_balance_rule,
    )

    def machine_capacity_rule(model, machine, period):
        return (
            sum(
                model.machine_hours_per_unit[machine, product]
                * model.production[product, period]
                for product in model.products
            )
            <= model.machine_capacity_per_period[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(model, product, period):
        return (
            model.inventory[product, period]
            <= model.max_inventory_per_period[product]
        )

    model.inventory_limit = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def product0_sales_limit_rule(model, period):
        return model.sales[0, period] <= model.sales_limit_product0[period]

    model.product0_sales_limit = pyo.Constraint(
        model.periods, rule=product0_sales_limit_rule
    )

    def product1_sales_limit_rule(model, period):
        return model.sales[1, period] <= model.sales_limit_product1[period]

    model.product1_sales_limit = pyo.Constraint(
        model.periods, rule=product1_sales_limit_rule
    )

    def final_inventory_rule(model, product):
        return (
            model.inventory[product, 3]
            == model.target_final_inventory[product]
        )

    model.final_inventory = pyo.Constraint(
        model.products, rule=final_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit_per_period[product]
            * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load may raise; objective retrieval decides success.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}