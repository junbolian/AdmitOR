# IR: {"sets":{"products":[0,1,2,3],"periods":[0,1,2,3,4,5],"machines":["grinder","drill","borer"]},"params":{"profit_per_unit":"[product]","holding_cost":"scalar","grinder_capacity":"[period]","drill_capacity":"[period]","borer_capacity":"[period]","machine_time":"4x3 product-by-machine array or 3x4 machine-by-product array; machine order grinder, drill, borer; alternatively machine-name-keyed rows","max_inventory":"scalar","max_sales":"[product][period]","final_inventory":"scalar"},"variables":{"production[i,t]":"continuous nonnegative","sales[i,t]":"continuous nonnegative","inventory[i,t]":"continuous nonnegative"},"constraints":["production[i,0] = sales[i,0] + inventory[i,0]","inventory[i,t-1] + production[i,t] = sales[i,t] + inventory[i,t] for t > 0","sum_i machine_time[k,i]*production[i,t] <= capacity[k,t]","inventory[i,t] <= max_inventory","sales[i,t] <= max_sales[i,t]","inventory[i,5] = final_inventory"],"objective":"maximize sum_i,t (profit_per_unit[i]*sales[i,t] - holding_cost*inventory[i,t])"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    machine_time = params["machine_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    machine_names = ("grinder", "drill", "borer")
    capacities = {
        "grinder": grinder_capacity,
        "drill": drill_capacity,
        "borer": borer_capacity,
    }

    # Normalize machine-time data to (machine name, product) coefficients.
    if isinstance(machine_time, Mapping) and all(
        machine_name in machine_time for machine_name in machine_names
    ):
        time_coefficients = {
            (machine_name, product): machine_time[machine_name][product]
            for machine_name in machine_names
            for product in range(4)
        }
    elif len(machine_time) == 4:
        time_coefficients = {
            (machine_name, product): machine_time[product][machine_position]
            for machine_position, machine_name in enumerate(machine_names)
            for product in range(4)
        }
    elif len(machine_time) == 3:
        time_coefficients = {
            (machine_name, product): machine_time[machine_position][product]
            for machine_position, machine_name in enumerate(machine_names)
            for product in range(4)
        }
    else:
        raise ValueError(
            "machine_time must be a 4x3 product-by-machine array, "
            "a 3x4 machine-by-product array, or machine-name-keyed rows."
        )

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 5)
    model.machines = pyo.Set(initialize=machine_names, ordered=True)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def balance_rule(mod, product, period):
        if period == 0:
            return (
                mod.production[product, period]
                == mod.sales[product, period] + mod.inventory[product, period]
            )
        return (
            mod.inventory[product, period - 1] + mod.production[product, period]
            == mod.sales[product, period] + mod.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def capacity_rule(mod, machine, period):
        return (
            sum(
                time_coefficients[machine, product]
                * mod.production[product, period]
                for product in mod.products
            )
            <= capacities[machine][period]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mod, product, period: (
            mod.inventory[product, period] <= max_inventory
        ),
    )

    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mod, product, period: (
            mod.sales[product, period] <= max_sales[product][period]
        ),
    )

    model.ending_inventory = pyo.Constraint(
        model.products,
        rule=lambda mod, product: mod.inventory[product, 5] == final_inventory,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit_per_unit[product] * model.sales[product, period]
            - holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
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