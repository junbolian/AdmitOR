# IR: {"sets":{"products":[0,1],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":["profit_p0","profit_p1","holding_cost","grinder_capacity","drill_capacity","borer_capacity","grind_hours_per_unit_p0","grind_hours_per_unit_p1","drill_hours_per_unit_p0","drill_hours_per_unit_p1","bore_hours_per_unit_p0","bore_hours_per_unit_p1","inventory_limit","sales_limit_p0","sales_limit_p1","target_inventory"],"input_structure":{"sales_limit_p0":"sequence or mapping indexed by period","sales_limit_p1":"sequence or mapping indexed by period","other_params":"scalars"},"variables":{"production[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals"},"constraints":{"initial_balance":"production[p,0] = sales[p,0] + inventory[p,0]","inventory_balance":"inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t], t=1,2,3","machine_capacity":"sum(hours[r,p]*production[p,t] for p) <= capacity[r]","inventory_capacity":"inventory[p,t] <= inventory_limit","sales_capacity":"sales[p,t] <= sales_limit[p,t]","ending_inventory":"inventory[p,3] = target_inventory"},"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p,t)"}

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
            0: params["profit_p0"],
            1: params["profit_p1"],
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
    model.hours = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grinder", 0): params["grind_hours_per_unit_p0"],
            ("grinder", 1): params["grind_hours_per_unit_p1"],
            ("drill", 0): params["drill_hours_per_unit_p0"],
            ("drill", 1): params["drill_hours_per_unit_p1"],
            ("borer", 0): params["bore_hours_per_unit_p0"],
            ("borer", 1): params["bore_hours_per_unit_p1"],
        },
    )
    model.inventory_limit = pyo.Param(initialize=params["inventory_limit"])
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): params[
                "sales_limit_p0" if product == 0 else "sales_limit_p1"
            ][period]
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

    def initial_balance_rule(instance, product):
        return (
            instance.production[product, 0]
            == instance.sales[product, 0] + instance.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(instance, product, period):
        if period == 0:
            return pyo.Constraint.Skip
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
                instance.hours[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_capacity_rule(instance, product, period):
        return (
            instance.inventory[product, period]
            <= instance.inventory_limit
        )

    model.inventory_capacity = pyo.Constraint(
        model.products, model.periods, rule=inventory_capacity_rule
    )

    def sales_capacity_rule(instance, product, period):
        return (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        )

    model.sales_capacity = pyo.Constraint(
        model.products, model.periods, rule=sales_capacity_rule
    )

    def ending_inventory_rule(instance, product):
        return (
            instance.inventory[product, 3] == instance.target_inventory
        )

    model.ending_inventory = pyo.Constraint(
        model.products, rule=ending_inventory_rule
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}