# IR: {
#   "sets": {"products": [0, 1, 2], "periods": [0, 1, 2, 3], "machines": ["grinder", "drill", "borer"]},
#   "params": {
#     "profit_per_unit": "product-indexed profits",
#     "holding_cost": "scalar holding cost",
#     "grinder_capacity": "scalar or period-indexed capacities",
#     "drill_capacity": "scalar or period-indexed capacities",
#     "borer_capacity": "scalar or period-indexed capacities; overridden to zero in period 2",
#     "max_inventory": "scalar inventory bound per product and period",
#     "max_sales_p0": "period-indexed sales bounds for product 0",
#     "max_sales_p1": "period-indexed sales bounds for product 1",
#     "max_sales_p2": "period-indexed sales bounds for product 2",
#     "final_inventory_target": "scalar terminal inventory for each product",
#     "grinder_time_p0": "grinder time for product 0",
#     "drill_time_p0": "drill time for product 0",
#     "borer_time_p0": "borer time for product 0",
#     "grinder_time_p1": "grinder time for product 1",
#     "drill_time_p1": "drill time for product 1",
#     "borer_time_p1": "borer time for product 1",
#     "grinder_time_p2": "grinder time for product 2",
#     "drill_time_p2": "drill time for product 2",
#     "borer_time_p2": "borer time for product 2"
#   },
#   "variables": {"production[p,t]": "nonnegative continuous", "sales[p,t]": "nonnegative continuous", "inventory[p,t]": "nonnegative continuous"},
#   "constraints": [
#     "production[p,0] = sales[p,0] + inventory[p,0] for every product p",
#     "inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for every product p and period t > 0",
#     "sum(processing_time[k,p] * production[p,t] for p) <= available_capacity[k,t] for every machine k and period t; borer capacity is zero in period 2",
#     "inventory[p,t] <= max_inventory for every product p and period t",
#     "sales[p,t] <= max_sales_p[p][t] for every product p and period t",
#     "inventory[p,3] = final_inventory_target for every product p"
#   ],
#   "objective": "maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p,t)"
# }

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"],
        ordered=True,
    )

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.unit_holding_cost = pyo.Param(
        initialize=params["holding_cost"]
    )
    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory"]
    )
    model.terminal_inventory = pyo.Param(
        initialize=params["final_inventory_target"]
    )

    capacity_inputs = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }

    def capacity_value(machine, period):
        supplied_capacity = capacity_inputs[machine]
        if machine == "borer" and period == 2:
            return 0
        if isinstance(supplied_capacity, Number):
            return supplied_capacity
        return supplied_capacity[period]

    model.available_capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): capacity_value(machine, period)
            for machine in model.machines
            for period in model.periods
        },
    )

    sales_inputs = {
        0: params["max_sales_p0"],
        1: params["max_sales_p1"],
        2: params["max_sales_p2"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_inputs[product][period]
            for product in model.products
            for period in model.periods
        },
    )

    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grinder", 0): params["grinder_time_p0"],
            ("drill", 0): params["drill_time_p0"],
            ("borer", 0): params["borer_time_p0"],
            ("grinder", 1): params["grinder_time_p1"],
            ("drill", 1): params["drill_time_p1"],
            ("borer", 1): params["borer_time_p1"],
            ("grinder", 2): params["grinder_time_p2"],
            ("drill", 2): params["drill_time_p2"],
            ("borer", 2): params["borer_time_p2"],
        },
    )

    model.production = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.sales = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.inventory = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(instance, product, period):
        if period == 0:
            return (
                instance.production[product, period]
                == instance.sales[product, period]
                + instance.inventory[product, period]
            )
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.periods,
        rule=balance_rule,
    )

    def machine_capacity_rule(instance, machine, period):
        return (
            sum(
                instance.processing_time[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.available_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines,
        model.periods,
        rule=machine_capacity_rule,
    )

    model.inventory_capacity_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period]
            <= instance.inventory_limit
        ),
    )

    model.sales_capacity_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        ),
    )

    model.final_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 3]
            == instance.terminal_inventory
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
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}