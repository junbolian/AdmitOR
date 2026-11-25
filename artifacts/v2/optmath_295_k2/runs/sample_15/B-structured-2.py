# IR: {"sets":{"P":[0,1],"T":[0,1,2,3],"R":["grind","drill","bore"]},"params":["profit_p0","profit_p1","holding_cost","grinder_capacity","drill_capacity","borer_capacity","grind_hours_per_unit_p0","grind_hours_per_unit_p1","drill_hours_per_unit_p0","drill_hours_per_unit_p1","bore_hours_per_unit_p0","bore_hours_per_unit_p1","inventory_limit","sales_limit_p0","sales_limit_p1","target_inventory"],"input_structure":{"sales_limit_p0":"sequence or mapping indexed by T","sales_limit_p1":"sequence or mapping indexed by T","other_params":"scalars"},"variables":{"production[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in {1,2,3}","sum(hours[r,p] * production[p,t] for p in P) <= capacity[r] for r in R, t in T","inventory[p,t] <= inventory_limit for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = target_inventory for p in P"],"objective":"maximize sum(profit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grind", "drill", "bore"], ordered=True
    )

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            0: params["profit_p0"],
            1: params["profit_p1"],
        },
    )
    model.holding_charge = pyo.Param(initialize=params["holding_cost"])
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize={
            "grind": params["grinder_capacity"],
            "drill": params["drill_capacity"],
            "bore": params["borer_capacity"],
        },
    )
    model.processing_hours = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("grind", 0): params["grind_hours_per_unit_p0"],
            ("grind", 1): params["grind_hours_per_unit_p1"],
            ("drill", 0): params["drill_hours_per_unit_p0"],
            ("drill", 1): params["drill_hours_per_unit_p1"],
            ("bore", 0): params["bore_hours_per_unit_p0"],
            ("bore", 1): params["bore_hours_per_unit_p1"],
        },
    )
    model.storage_limit = pyo.Param(initialize=params["inventory_limit"])
    model.ending_target = pyo.Param(initialize=params["target_inventory"])

    sales_limits = {
        0: params["sales_limit_p0"],
        1: params["sales_limit_p1"],
    }
    model.sales_ceiling = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
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

    def balance_rule(block, product, period):
        if period == 0:
            return (
                block.production[product, period]
                == block.sales[product, period]
                + block.inventory[product, period]
            )
        return (
            block.inventory[product, period - 1]
            + block.production[product, period]
            == block.sales[product, period]
            + block.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def capacity_rule(block, machine, period):
        return (
            sum(
                block.processing_hours[machine, product]
                * block.production[product, period]
                for product in block.products
            )
            <= block.machine_capacity[machine]
        )

    model.capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )

    model.inventory_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.inventory[product, period] <= block.storage_limit
        ),
    )
    model.sales_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda block, product, period: (
            block.sales[product, period]
            <= block.sales_ceiling[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.products,
        rule=lambda block, product: (
            block.inventory[product, 3] == block.ending_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_charge * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}