# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3],"K":["grinder","drill","borer"]},"params":{"profit[p]":"params[profit_product{p}]","holding_cost":"params[holding_cost]","capacity[k]":"params[{k}_capacity]","hours[k,p]":"params[{k}_hours_per_unit][p]","inventory_capacity":"params[inventory_capacity]","sales_limit[p,t]":"params[sales_limit_product{p}][t]","final_inventory_target":"params[final_inventory_target]"},"variables":{"production[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T with t>0","sum(hours[k,p]*production[p,t] for p in P) <= capacity[k] for k in K, t in T","inventory[p,t] <= inventory_capacity for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = final_inventory_target for p in P"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 3)
    model.K = pyo.Set(initialize=["grinder", "drill", "borer"], ordered=True)

    profits = [
        params["profit_product0"],
        params["profit_product1"],
        params["profit_product2"],
    ]
    capacities = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }
    machine_hours = {
        "grinder": params["grinder_hours_per_unit"],
        "drill": params["drill_hours_per_unit"],
        "borer": params["borer_hours_per_unit"],
    }
    sales_limits = [
        params["sales_limit_product0"],
        params["sales_limit_product1"],
        params["sales_limit_product2"],
    ]

    model.profit = pyo.Param(
        model.P,
        initialize={product: profits[product] for product in model.P},
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.capacity = pyo.Param(model.K, initialize=capacities)
    model.hours = pyo.Param(
        model.K,
        model.P,
        initialize={
            (machine, product): machine_hours[machine][product]
            for machine in model.K
            for product in model.P
        },
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"]
    )
    model.sales_limit = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.P
            for period in model.T
        },
    )
    model.final_inventory_target = pyo.Param(
        initialize=params["final_inventory_target"]
    )

    model.production = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

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
        model.P, model.T, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        return (
            sum(
                mdl.hours[machine, product] * mdl.production[product, period]
                for product in mdl.P
            )
            <= mdl.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.K, model.T, rule=machine_capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_capacity
        ),
    )
    model.sales_limit_constraint = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_limit[product, period]
        ),
    )
    model.final_inventory_constraint = pyo.Constraint(
        model.P,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.final_inventory_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.P
            for period in model.T
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}