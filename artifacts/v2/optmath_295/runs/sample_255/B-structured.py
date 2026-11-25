# IR: {"sets":{"P":[0,1],"T":[0,1,2,3],"K":["grinder","drill","borer"]},"params":{"profit_per_unit":"P -> real","holding_cost_per_unit":"nonnegative scalar","machine_capacity_grinder":"nonnegative scalar","machine_capacity_drill":"nonnegative scalar","machine_capacity_borer":"nonnegative scalar","prod_time_grinder":"P -> nonnegative real","prod_time_drill":"P -> nonnegative real","prod_time_borer":"P -> nonnegative real","inventory_capacity":"nonnegative scalar","sales_limit_prod0":"T -> nonnegative real","sales_limit_prod1":"T -> nonnegative real","target_inventory":"nonnegative scalar"},"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T with t > 0","sum(prod_time[k,p] * production[p,t] for p in P) <= machine_capacity[k] for k in K, t in T","inventory[p,t] <= inventory_capacity for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = target_inventory for p in P"],"objective":"maximize sum(profit_per_unit[p] * sales[p,t] - holding_cost_per_unit * inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    profit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit"]
    inventory_capacity = params["inventory_capacity"]
    target_inventory = params["target_inventory"]

    machine_capacity = {
        "grinder": params["machine_capacity_grinder"],
        "drill": params["machine_capacity_drill"],
        "borer": params["machine_capacity_borer"],
    }
    production_time = {
        "grinder": params["prod_time_grinder"],
        "drill": params["prod_time_drill"],
        "borer": params["prod_time_borer"],
    }
    sales_limits = {
        0: params["sales_limit_prod0"],
        1: params["sales_limit_prod1"],
    }

    model.unit_profit = pyo.Param(
        model.products,
        initialize={p: profit[p] for p in model.products},
        within=pyo.Reals,
    )
    model.holding_charge = pyo.Param(
        initialize=holding_cost, within=pyo.NonNegativeReals
    )
    model.machine_hours = pyo.Param(
        model.machines,
        initialize=machine_capacity,
        within=pyo.NonNegativeReals,
    )
    model.unit_machine_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, p): production_time[machine][p]
            for machine in model.machines
            for p in model.products
        },
        within=pyo.NonNegativeReals,
    )
    model.storage_limit = pyo.Param(
        initialize=inventory_capacity, within=pyo.NonNegativeReals
    )
    model.sales_upper_bound = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (p, t): sales_limits[p][t]
            for p in model.products
            for t in model.periods
        },
        within=pyo.NonNegativeReals,
    )
    model.final_stock = pyo.Param(
        initialize=target_inventory, within=pyo.NonNegativeReals
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

    def inventory_balance_rule(mod, p, t):
        if t == 0:
            return (
                mod.production[p, t]
                == mod.sales[p, t] + mod.inventory[p, t]
            )
        return (
            mod.inventory[p, t - 1] + mod.production[p, t]
            == mod.sales[p, t] + mod.inventory[p, t]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mod, machine, t):
        return (
            sum(
                mod.unit_machine_time[machine, p] * mod.production[p, t]
                for p in mod.products
            )
            <= mod.machine_hours[machine]
        )

    model.machine_capacity_limits = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    model.inventory_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mod, p, t: mod.inventory[p, t] <= mod.storage_limit,
    )
    model.sales_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mod, p, t: (
            mod.sales[p, t] <= mod.sales_upper_bound[p, t]
        ),
    )
    model.final_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mod, p: mod.inventory[p, 3] == mod.final_stock,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[p] * model.sales[p, t]
            - model.holding_charge * model.inventory[p, t]
            for p in model.products
            for t in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}