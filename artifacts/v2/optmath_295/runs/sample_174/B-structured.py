# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit_product0":"scalar","profit_product1":"scalar","holding_cost":"scalar","grinder_req_product0":"scalar","grinder_req_product1":"scalar","drill_req_product0":"scalar","drill_req_product1":"scalar","borer_req_product0":"scalar","borer_req_product1":"scalar","grinder_capacity":"period-indexed sequence or mapping","drill_capacity":"period-indexed sequence or mapping","borer_capacity":"period-indexed sequence or mapping","inventory_limit":"scalar","sales_limit_product0":"period-indexed sequence or mapping","sales_limit_product1":"period-indexed sequence or mapping","target_inventory_product0":"scalar","target_inventory_product1":"scalar"},"variables":{"production[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum(requirement[k,p] * production[p,t] for p) <= capacity[k,t] for each machine k and period t","inventory[p,t] <= inventory_limit for each product p and period t","sales[p,t] <= sales_limit[p,t] for each product p and period t","inventory[p,3] = target_inventory[p] for each product p"],"objective":"maximize sum(profit[p] * sales[p,t] - holding_cost * inventory[p,t] for all products p and periods t)"}

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
            0: params["profit_product0"],
            1: params["profit_product1"],
        },
    )
    model.unit_holding_cost = pyo.Param(initialize=params["holding_cost"])

    model.machine_requirement = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grinder", 0): params["grinder_req_product0"],
            ("grinder", 1): params["grinder_req_product1"],
            ("drill", 0): params["drill_req_product0"],
            ("drill", 1): params["drill_req_product1"],
            ("borer", 0): params["borer_req_product0"],
            ("borer", 1): params["borer_req_product1"],
        },
    )

    capacity_data = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
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

    model.inventory_ceiling = pyo.Param(initialize=params["inventory_limit"])

    sales_limit_data = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    model.sales_ceiling = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limit_data[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.ending_inventory_target = pyo.Param(
        model.products,
        initialize={
            0: params["target_inventory_product0"],
            1: params["target_inventory_product1"],
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
                mdl.machine_requirement[machine, product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.machine_capacity[machine, period]
        )

    model.capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )

    model.inventory_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_ceiling
        ),
    )
    model.sales_bounds = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_ceiling[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.ending_inventory_target[product]
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}