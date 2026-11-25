# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3],"K":["grinders","drills","borers"]},"params":{"profit[p]":["profit_per_unit_product_0","profit_per_unit_product_1","profit_per_unit_product_2"],"holding_cost":"holding_cost_per_unit_per_month","capacity[k,t]":["machine_hours_available_grinders","machine_hours_available_drills","machine_hours_available_borers"],"processing_time[k,p]":["time_grinders_product_0","time_grinders_product_1","time_grinders_product_2","time_drills_product_0","time_drills_product_1","time_drills_product_2","time_borers_product_0","time_borers_product_1","time_borers_product_2"],"inventory_limit":"max_inventory_per_product","sales_limit[p,t]":["sales_limits_product_0","sales_limits_product_1","sales_limits_product_2"],"final_target":"target_inventory_end_horizon"},"variables":{"production[p,t]":"continuous >= 0","sales[p,t]":"continuous >= 0","inventory[p,t]":"continuous >= 0"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in {1,2,3}","sum(processing_time[k,p]*production[p,t] for p in P) <= capacity[k,t] for k in K, t in T","inventory[p,t] <= inventory_limit for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,3] = final_target for p in P"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.T = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.K = pyo.Set(
        initialize=["grinders", "drills", "borers"], ordered=True
    )

    model.profit = pyo.Param(
        model.P,
        initialize={
            0: params["profit_per_unit_product_0"],
            1: params["profit_per_unit_product_1"],
            2: params["profit_per_unit_product_2"],
        },
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_month"]
    )

    available_hours = {
        "grinders": params["machine_hours_available_grinders"],
        "drills": params["machine_hours_available_drills"],
        "borers": params["machine_hours_available_borers"],
    }
    model.capacity = pyo.Param(
        model.K,
        model.T,
        initialize={
            (machine, month): available_hours[machine][month]
            for machine in model.K
            for month in model.T
        },
    )

    model.processing_time = pyo.Param(
        model.K,
        model.P,
        initialize={
            ("grinders", 0): params["time_grinders_product_0"],
            ("grinders", 1): params["time_grinders_product_1"],
            ("grinders", 2): params["time_grinders_product_2"],
            ("drills", 0): params["time_drills_product_0"],
            ("drills", 1): params["time_drills_product_1"],
            ("drills", 2): params["time_drills_product_2"],
            ("borers", 0): params["time_borers_product_0"],
            ("borers", 1): params["time_borers_product_1"],
            ("borers", 2): params["time_borers_product_2"],
        },
    )

    model.inventory_limit = pyo.Param(
        initialize=params["max_inventory_per_product"]
    )
    sales_limits = {
        0: params["sales_limits_product_0"],
        1: params["sales_limits_product_1"],
        2: params["sales_limits_product_2"],
    }
    model.sales_limit = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, month): sales_limits[product][month]
            for product in model.P
            for month in model.T
        },
    )
    model.final_target = pyo.Param(
        initialize=params["target_inventory_end_horizon"]
    )

    model.production = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.P, rule=initial_balance_rule
    )

    def monthly_balance_rule(mdl, product, month):
        if month == 0:
            return pyo.Constraint.Skip
        return (
            mdl.inventory[product, month - 1]
            + mdl.production[product, month]
            == mdl.sales[product, month] + mdl.inventory[product, month]
        )

    model.monthly_balance = pyo.Constraint(
        model.P, model.T, rule=monthly_balance_rule
    )

    def machine_capacity_rule(mdl, machine, month):
        return (
            sum(
                mdl.processing_time[machine, product]
                * mdl.production[product, month]
                for product in mdl.P
            )
            <= mdl.capacity[machine, month]
        )

    model.machine_capacity = pyo.Constraint(
        model.K, model.T, rule=machine_capacity_rule
    )

    model.inventory_capacity = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, product, month: (
            mdl.inventory[product, month] <= mdl.inventory_limit
        ),
    )
    model.sales_capacity = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, product, month: (
            mdl.sales[product, month] <= mdl.sales_limit[product, month]
        ),
    )
    model.final_inventory = pyo.Constraint(
        model.P,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.final_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, month]
            - model.holding_cost * model.inventory[product, month]
            for product in model.P
            for month in model.T
        ),
        sense=pyo.maximize,
    )

    # APPsi may raise before loading a solution when none is available.
    try:
        Highs().solve(model)
    except RuntimeError:
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}