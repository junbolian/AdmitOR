# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3],"machines":[0,1,2]},"params":{"profit_per_unit":"[product]","holding_cost_per_unit_per_period":"scalar","machine_capacity":"[machine][period]","processing_time":"[machine][product]","max_inventory":"scalar","max_sales":"[product][period]","target_final_inventory":"scalar"},"variables":{"production[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum(processing_time[k][p] * production[p,t] for p) <= machine_capacity[k][t] for each machine k and period t","inventory[p,t] <= max_inventory for each product p and period t","sales[p,t] <= max_sales[p][t] for each product p and period t","inventory[p,3] = target_final_inventory for each product p"],"objective":"maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost_per_unit_per_period * inventory[p,t] for each product p and period t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 3)
    model.machines = pyo.RangeSet(0, 2)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize=lambda mdl, machine, period: params["machine_capacity"][
            machine
        ][period],
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize=lambda mdl, machine, product: params["processing_time"][
            machine
        ][product],
    )
    model.max_inventory = pyo.Param(
        initialize=params["max_inventory"],
    )
    model.max_sales = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: params["max_sales"][product][
            period
        ],
    )
    model.target_final_inventory = pyo.Param(
        initialize=params["target_final_inventory"],
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

    def inventory_balance_rule(mdl, product, period):
        if period == 0:
            return (
                mdl.production[product, period]
                == mdl.sales[product, period] + mdl.inventory[product, period]
            )
        return (
            mdl.inventory[product, period - 1] + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.processing_time[machine, product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.machine_capacity[machine, period]
        )

    model.machine_capacity_limit = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.max_inventory
        ),
    )
    model.sales_limit = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.max_sales[product, period]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.target_final_inventory
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
        # Appsi raises this specific error when no feasible solution can load.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}