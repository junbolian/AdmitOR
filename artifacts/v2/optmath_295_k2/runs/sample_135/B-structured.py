# {
#   "sets": {"P": [0, 1], "T": [0, 1, 2, 3], "R": ["grinder", "drill", "borer"]},
#   "params": ["profit_per_unit_p0", "profit_per_unit_p1", "holding_cost_per_unit_per_period", "grinder_capacity_period", "drill_capacity_period", "borer_capacity_period", "grinder_hours_per_unit_p0", "grinder_hours_per_unit_p1", "drill_hours_per_unit", "borer_hours_per_unit", "max_inventory_per_product_per_period", "max_sales_p0_period", "max_sales_p1_period", "final_inventory_p0", "final_inventory_p1"],
#   "decision_variables": {"production[p,t]": "nonnegative continuous", "sales[p,t]": "nonnegative continuous", "inventory[p,t]": "nonnegative continuous"},
#   "constraints": [
#     "For each p: production[p,0] = sales[p,0] + inventory[p,0] (zero initial inventory).",
#     "For each p and t > 0: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t].",
#     "For each r,t: sum_p machine_hours[r,p] * production[p,t] <= machine_capacity[r,t].",
#     "For each p,t: inventory[p,t] <= max_inventory_per_product_per_period.",
#     "For each p,t: sales[p,t] <= max_sales[p,t].",
#     "For each p: inventory[p,3] = final_inventory[p]."
#   ],
#   "objective": "Maximize sum_{p,t}(profit_per_unit[p] * sales[p,t] - holding_cost_per_unit_per_period * inventory[p,t]); holding cost applies to ending inventory in all four periods."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            0: params["profit_per_unit_p0"],
            1: params["profit_per_unit_p1"],
        },
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"]
    )
    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory_per_product_per_period"]
    )

    capacity_data = {
        "grinder": params["grinder_capacity_period"],
        "drill": params["drill_capacity_period"],
        "borer": params["borer_capacity_period"],
    }
    model.machine_capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): capacity_data[machine][period]
            for machine in model.machines
            for period in model.periods
        },
    )
    model.machine_hours = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grinder", 0): params["grinder_hours_per_unit_p0"],
            ("grinder", 1): params["grinder_hours_per_unit_p1"],
            ("drill", 0): params["drill_hours_per_unit"],
            ("drill", 1): params["drill_hours_per_unit"],
            ("borer", 0): params["borer_hours_per_unit"],
            ("borer", 1): params["borer_hours_per_unit"],
        },
    )

    sales_data = {
        0: params["max_sales_p0_period"],
        1: params["max_sales_p1_period"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_data[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.required_final_inventory = pyo.Param(
        model.products,
        initialize={
            0: params["final_inventory_p0"],
            1: params["final_inventory_p1"],
        },
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

    def inventory_balance_rule(instance, product, period):
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
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(instance, machine, period):
        return (
            sum(
                instance.machine_hours[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.machine_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    model.inventory_capacity_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period] <= instance.inventory_limit
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
            == instance.required_final_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}