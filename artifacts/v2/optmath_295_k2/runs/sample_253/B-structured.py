# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit_per_unit":"vector[products]","holding_cost":"scalar","grinder_capacity":"scalar","drill_capacity":"scalar","borer_capacity":"scalar","grinder_hours_per_unit":"vector[products]","drill_hours_per_unit":"vector[products]","borer_hours_per_unit":"vector[products]","inventory_limit":"scalar","sales_limit_product0":"vector[periods]","sales_limit_product1":"vector[periods]","target_inventory":"scalar"},"variables":{"production[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum(hours_per_unit[k,p] * production[p,t] for p) <= capacity[k] for each machine k and period t","inventory[p,t] <= inventory_limit for each product p and period t","sales[p,t] <= sales_limit_product0[t] if p=0, otherwise sales_limit_product1[t]","inventory[p,3] = target_inventory for each product p"],"objective":"maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for each product p and period t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    profit_per_unit = params["profit_per_unit"]
    hours_per_unit = {
        "grinder": params["grinder_hours_per_unit"],
        "drill": params["drill_hours_per_unit"],
        "borer": params["borer_hours_per_unit"],
    }
    capacities = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }
    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profit_per_unit[product],
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        initialize=params["holding_cost"], within=pyo.NonNegativeReals
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.machine_unit_hours = pyo.Param(
        model.machines,
        model.products,
        initialize=lambda mdl, machine, product: hours_per_unit[machine][product],
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_limit"], within=pyo.NonNegativeReals
    )
    model.sales_capacity = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: sales_limits[product][period],
        within=pyo.NonNegativeReals,
    )
    model.required_ending_inventory = pyo.Param(
        initialize=params["target_inventory"], within=pyo.NonNegativeReals
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

    def balance_rule(mdl, product, period):
        if period == 0:
            return (
                mdl.production[product, period]
                == mdl.sales[product, period] + mdl.inventory[product, period]
            )
        return (
            mdl.inventory[product, period - 1]
            + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.machine_unit_hours[machine, product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.machine_capacity[machine]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )
    model.inventory_limit_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_capacity
        ),
    )
    model.sales_limit_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_capacity[product, period]
        ),
    )
    model.ending_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.required_ending_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.inventory_holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this expected error when it cannot load a solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}