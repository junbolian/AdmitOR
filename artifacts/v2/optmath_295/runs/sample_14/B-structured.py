# IR: {"sets":{"products":[0,1,2,3],"periods":[0,1,2,3,4],"machines":["grinders","drills","borers"]},"params":{"profit_per_unit":"vector[products]","holding_cost_per_unit":"scalar","machine_hours_grinders":"scalar","machine_hours_drills":"scalar","machine_hours_borers":"scalar","borer_hours_period0":"scalar","time_per_unit":"matrix[products,machines], columns ordered grinders,drills,borers","inventory_capacity":"scalar","sales_limit":"matrix[products,periods]","target_inventory_end":"vector[products]"},"variables":{"production[product,period]":"NonNegativeReals","inventory[product,period]":"NonNegativeReals","sales[product,period]":"NonNegativeReals"},"constraints":["For each product: production[product,0] = sales[product,0] + inventory[product,0].","For each product and period > 0: inventory[product,period-1] + production[product,period] = sales[product,period] + inventory[product,period].","For each period: sum_product(time_per_unit[product,grinders] * production[product,period]) <= machine_hours_grinders.","For each period: sum_product(time_per_unit[product,drills] * production[product,period]) <= machine_hours_drills.","For each period: sum_product(time_per_unit[product,borers] * production[product,period]) <= (borer_hours_period0 if period = 0 else machine_hours_borers).","For each product and period: inventory[product,period] <= inventory_capacity.","For each product and period: sales[product,period] <= sales_limit[product,period].","For each product: inventory[product,4] = target_inventory_end[product]."],"objective":"Maximize sum_product,period(profit_per_unit[product] * sales[product,period] - holding_cost_per_unit * inventory[product,period])."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 4)
    model.machines = pyo.Set(
        initialize=["grinders", "drills", "borers"], ordered=True
    )

    machine_columns = {"grinders": 0, "drills": 1, "borers": 2}

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
    )
    model.holding_cost_per_unit = pyo.Param(
        initialize=params["holding_cost_per_unit"]
    )
    model.machine_hours_grinders = pyo.Param(
        initialize=params["machine_hours_grinders"]
    )
    model.machine_hours_drills = pyo.Param(
        initialize=params["machine_hours_drills"]
    )
    model.machine_hours_borers = pyo.Param(
        initialize=params["machine_hours_borers"]
    )
    model.borer_hours_period0 = pyo.Param(
        initialize=params["borer_hours_period0"]
    )
    model.time_per_unit = pyo.Param(
        model.products,
        model.machines,
        initialize={
            (product, machine): params["time_per_unit"][product][
                machine_columns[machine]
            ]
            for product in model.products
            for machine in model.machines
        },
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"]
    )
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): params["sales_limit"][product][period]
            for product in model.products
            for period in model.periods
        },
    )
    model.target_inventory_end = pyo.Param(
        model.products,
        initialize={
            product: params["target_inventory_end"][product]
            for product in model.products
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

    def inventory_balance_rule(model, product, period):
        if period == 0:
            return (
                model.production[product, period]
                == model.sales[product, period]
                + model.inventory[product, period]
            )
        return (
            model.inventory[product, period - 1]
            + model.production[product, period]
            == model.sales[product, period]
            + model.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(model, machine, period):
        if machine == "grinders":
            capacity = model.machine_hours_grinders
        elif machine == "drills":
            capacity = model.machine_hours_drills
        elif period == 0:
            capacity = model.borer_hours_period0
        else:
            capacity = model.machine_hours_borers

        return (
            sum(
                model.time_per_unit[product, machine]
                * model.production[product, period]
                for product in model.products
            )
            <= capacity
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(model, product, period):
        return (
            model.inventory[product, period]
            <= model.inventory_capacity
        )

    model.inventory_limit = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(model, product, period):
        return (
            model.sales[product, period]
            <= model.sales_limit[product, period]
        )

    model.sales_upper_bound = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def target_inventory_rule(model, product):
        return (
            model.inventory[product, 4]
            == model.target_inventory_end[product]
        )

    model.terminal_inventory = pyo.Constraint(
        model.products, rule=target_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost_per_unit * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}