# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4],"machines":["grinders","drills","borers"]},"params":{"profit_per_unit":"product-indexed","holding_cost":"scalar","machine_hours_grinders":"period-indexed","machine_hours_drills":"period-indexed","machine_hours_borers":"period-indexed","time_req_grinders":"product-indexed","time_req_drills":"product-indexed","time_req_borers":"product-indexed","inventory_capacity":"scalar, per product per period","sales_limit_p0":"period-indexed","sales_limit_p1":"period-indexed","sales_limit_p2":"period-indexed","target_inventory":"scalar, per product"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t>0","sum_p(time_req[k,p]*production[p,t]) <= machine_hours[k,t] for each machine k and period t","inventory[p,t] <= inventory_capacity for each product p and period t","sales[p,t] <= sales_limit[p,t] for each product p and period t","inventory[p,4] = target_inventory for each product p"],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.periods = pyo.RangeSet(0, 4)
    model.machines = pyo.Set(
        initialize=["grinders", "drills", "borers"], ordered=True
    )

    capacity_data = {
        "grinders": params["machine_hours_grinders"],
        "drills": params["machine_hours_drills"],
        "borers": params["machine_hours_borers"],
    }
    time_data = {
        "grinders": params["time_req_grinders"],
        "drills": params["time_req_drills"],
        "borers": params["time_req_borers"],
    }
    sales_data = {
        0: params["sales_limit_p0"],
        1: params["sales_limit_p1"],
        2: params["sales_limit_p2"],
    }

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.unit_holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.inventory_limit = pyo.Param(initialize=params["inventory_capacity"])
    model.final_inventory_target = pyo.Param(
        initialize=params["target_inventory"]
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): capacity_data[machine][period]
            for machine in model.machines
            for period in model.periods
        },
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product): time_data[machine][product]
            for machine in model.machines
            for product in model.products
        },
    )
    model.sales_cap = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_data[product][period]
            for product in model.products
            for period in model.periods
        },
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
                instance.processing_time[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.machine_capacity[machine, period]
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(instance, product, period):
        return (
            instance.inventory[product, period] <= instance.inventory_limit
        )

    model.inventory_limit_constraints = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(instance, product, period):
        return instance.sales[product, period] <= instance.sales_cap[
            product, period
        ]

    model.sales_limit_constraints = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def target_inventory_rule(instance, product):
        return (
            instance.inventory[product, 4]
            == instance.final_inventory_target
        )

    model.target_inventory_constraints = pyo.Constraint(
        model.products, rule=target_inventory_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}