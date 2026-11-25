# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit_product0":"scalar","profit_product1":"scalar","holding_cost":"scalar","grinder_capacity":"scalar","drill_capacity":"scalar","borer_capacity":"scalar","time_product0_grinder":"scalar","time_product0_drill":"scalar","time_product0_borer":"scalar","time_product1_grinder":"scalar","time_product1_drill":"scalar","time_product1_borer":"scalar","inventory_limit":"scalar","sales_limit_product0":"period-indexed sequence or mapping","sales_limit_product1":"period-indexed sequence or mapping","target_inventory":"scalar"},"variables":{"production[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t=1,2,3","sum_p time[p,k]*production[p,t] <= capacity[k] for each machine k and period t","inventory[p,t] <= inventory_limit","sales[p,t] <= sales_limit[p,t]","inventory[p,3] = target_inventory"],"objective":"maximize sum_{p,t}(profit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.profit = pyo.Param(
        model.products,
        initialize={
            0: params["profit_product0"],
            1: params["profit_product1"],
        },
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.capacity = pyo.Param(
        model.machines,
        initialize={
            "grinder": params["grinder_capacity"],
            "drill": params["drill_capacity"],
            "borer": params["borer_capacity"],
        },
    )
    model.processing_time = pyo.Param(
        model.products,
        model.machines,
        initialize={
            (0, "grinder"): params["time_product0_grinder"],
            (0, "drill"): params["time_product0_drill"],
            (0, "borer"): params["time_product0_borer"],
            (1, "grinder"): params["time_product1_grinder"],
            (1, "drill"): params["time_product1_drill"],
            (1, "borer"): params["time_product1_borer"],
        },
    )
    model.inventory_limit = pyo.Param(initialize=params["inventory_limit"])
    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.target_inventory = pyo.Param(initialize=params["target_inventory"])

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
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
                mdl.processing_time[product, machine]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= mdl.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    model.inventory_storage = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_limit
        ),
    )
    model.sales_restriction = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_limit[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.target_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}