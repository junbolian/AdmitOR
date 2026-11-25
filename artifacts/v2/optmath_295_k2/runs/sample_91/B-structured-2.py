# IR: {"sets":{"products":[0,1,2],"months":[0,1,2,3],"machines":["grinders","drills","borers"]},"params":{"profit[p]":"params['profit_per_unit_product_'+str(p)]","holding_cost":"params['holding_cost_per_unit_per_month']","capacity[k,t]":"params['machine_hours_available_'+k][t]","processing_time[k,p]":"params['time_'+k+'_product_'+str(p)]","inventory_capacity":"params['max_inventory_per_product']","sales_limit[p,t]":"params['sales_limits_product_'+str(p)][t]","final_inventory":"params['target_inventory_end_horizon']"},"variables":{"production[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each p and t in {1,2,3}","sum(processing_time[k,p]*production[p,t] for p) <= capacity[k,t] for each k,t","inventory[p,t] <= inventory_capacity for each p,t","sales[p,t] <= sales_limit[p,t] for each p,t","inventory[p,3] = final_inventory for each p"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost*inventory[p,t] for p,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_data = {
        0: params["profit_per_unit_product_0"],
        1: params["profit_per_unit_product_1"],
        2: params["profit_per_unit_product_2"],
    }
    holding_cost = params["holding_cost_per_unit_per_month"]

    capacity_data = {
        "grinders": params["machine_hours_available_grinders"],
        "drills": params["machine_hours_available_drills"],
        "borers": params["machine_hours_available_borers"],
    }

    processing_time_data = {
        ("grinders", 0): params["time_grinders_product_0"],
        ("grinders", 1): params["time_grinders_product_1"],
        ("grinders", 2): params["time_grinders_product_2"],
        ("drills", 0): params["time_drills_product_0"],
        ("drills", 1): params["time_drills_product_1"],
        ("drills", 2): params["time_drills_product_2"],
        ("borers", 0): params["time_borers_product_0"],
        ("borers", 1): params["time_borers_product_1"],
        ("borers", 2): params["time_borers_product_2"],
    }

    inventory_capacity = params["max_inventory_per_product"]
    sales_limit_data = {
        0: params["sales_limits_product_0"],
        1: params["sales_limits_product_1"],
        2: params["sales_limits_product_2"],
    }
    final_inventory = params["target_inventory_end_horizon"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.months = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.later_months = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinders", "drills", "borers"],
        ordered=True,
    )

    model.profit = pyo.Param(model.products, initialize=profit_data)
    model.holding_cost = pyo.Param(initialize=holding_cost)
    model.capacity = pyo.Param(
        model.machines,
        model.months,
        initialize={
            (machine, month): capacity_data[machine][month]
            for machine in model.machines
            for month in model.months
        },
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize=processing_time_data,
    )
    model.inventory_capacity = pyo.Param(initialize=inventory_capacity)
    model.sales_limit = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): sales_limit_data[product][month]
            for product in model.products
            for month in model.months
        },
    )
    model.final_inventory = pyo.Param(initialize=final_inventory)

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(model, product):
        return (
            model.production[product, 0]
            == model.sales[product, 0] + model.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def monthly_balance_rule(model, product, month):
        return (
            model.inventory[product, month - 1]
            + model.production[product, month]
            == model.sales[product, month] + model.inventory[product, month]
        )

    model.monthly_balance = pyo.Constraint(
        model.products, model.later_months, rule=monthly_balance_rule
    )

    def machine_capacity_rule(model, machine, month):
        return (
            sum(
                model.processing_time[machine, product]
                * model.production[product, month]
                for product in model.products
            )
            <= model.capacity[machine, month]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.months, rule=machine_capacity_rule
    )

    def inventory_limit_rule(model, product, month):
        return model.inventory[product, month] <= model.inventory_capacity

    model.inventory_limit = pyo.Constraint(
        model.products, model.months, rule=inventory_limit_rule
    )

    def sales_limit_rule(model, product, month):
        return model.sales[product, month] <= model.sales_limit[product, month]

    model.sales_upper_bound = pyo.Constraint(
        model.products, model.months, rule=sales_limit_rule
    )

    def terminal_inventory_rule(model, product):
        return model.inventory[product, 3] == model.final_inventory

    model.terminal_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, month]
            - model.holding_cost * model.inventory[product, month]
            for product in model.products
            for month in model.months
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