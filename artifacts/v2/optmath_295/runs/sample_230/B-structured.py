# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4,5],"machines":[0,1,2]},"params":{"profit_per_unit":"[product]","holding_cost":"scalar","grinder_hours":"[period]","drill_hours":"[period]","borer_hours":"[period]","machine_hours_per_unit":"[machine][product]; rows: grinders, drills, borers","max_inventory":"scalar or [product]","max_sales":"[period][product]","final_inventory":"scalar or [product]"},"variables":{"production[t,p]":"NonNegativeReals","sales[t,p]":"NonNegativeReals","inventory[t,p]":"NonNegativeReals"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p] for each p","inventory[t-1,p] + production[t,p] = sales[t,p] + inventory[t,p] for each t>0,p","sum(machine_hours_per_unit[k][p]*production[t,p] for p) <= capacity[k][t] for each k,t; capacity rows are grinder_hours, drill_hours, borer_hours","inventory[t,p] <= max_inventory[p] for each t,p; broadcast scalar","sales[t,p] <= max_sales[t][p] for each t,p","inventory[5,p] = final_inventory[p] for each p; broadcast scalar"],"objective":"maximize sum(profit_per_unit[p]*sales[t,p] - holding_cost*inventory[t,p] for t,p)","failure_handling":["If a required parameter is absent, return objective=null and status=missing_parameter:<key>; never invent missing numeric data","If HiGHS reports no feasible solution can be loaded, attempt objective evaluation; propagate other solver exceptions","Return optimal only if objective evaluation succeeds; otherwise return objective_unavailable"]}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_parameters = (
        "profit_per_unit",
        "holding_cost",
        "grinder_hours",
        "drill_hours",
        "borer_hours",
        "machine_hours_per_unit",
        "max_inventory",
        "max_sales",
        "final_inventory",
    )

    # Missing coefficients cannot be reconstructed without violating the
    # requirement that all numerical problem data come from params.
    for parameter_name in required_parameters:
        if parameter_name not in params:
            return {
                "objective": None,
                "status": f"missing_parameter:{parameter_name}",
            }

    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    capacity = (grinder_hours, drill_hours, borer_hours)

    def product_value(data, product):
        return data if isinstance(data, Number) else data[product]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 5)
    model.machines = pyo.RangeSet(0, 2)

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, period, product):
        if period == 0:
            return (
                instance.production[period, product]
                == instance.sales[period, product]
                + instance.inventory[period, product]
            )
        return (
            instance.inventory[period - 1, product]
            + instance.production[period, product]
            == instance.sales[period, product]
            + instance.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, model.products, rule=balance_rule
    )

    def capacity_rule(instance, machine, period):
        return (
            sum(
                machine_hours_per_unit[machine][product]
                * instance.production[period, product]
                for product in instance.products
            )
            <= capacity[machine][period]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda instance, period, product: (
            instance.inventory[period, product]
            <= product_value(max_inventory, product)
        ),
    )

    model.sales_limit = pyo.Constraint(
        model.periods,
        model.products,
        rule=lambda instance, period, product: (
            instance.sales[period, product] <= max_sales[period][product]
        ),
    )

    model.ending_inventory = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[5, product]
            == product_value(final_inventory, product)
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit_per_unit[product] * model.sales[period, product]
            - holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}