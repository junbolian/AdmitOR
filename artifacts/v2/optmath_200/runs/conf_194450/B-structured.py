# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3,4],"machines":["grinder","drill","borer"]},"params":{"profit_per_unit":"vector[product]","holding_cost_per_unit":"scalar","grinder_capacity":"scalar","drill_capacity":"scalar","borer_capacity":"scalar","machine_hours_product0":"vector[machine]","machine_hours_product1":"vector[machine]","machine_hours_product2":"vector[machine]","max_inventory_per_product":"scalar","sales_limit_product0":"vector[period]","sales_limit_product1":"vector[period]","sales_limit_product2":"vector[period]","target_inventory_end":"scalar"},"variables":{"production[product,period]":"nonnegative continuous","inventory[product,period]":"nonnegative continuous","sales[product,period]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for each product p","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for each product p and period t > 0","sum_p(machine_hours[p,k] * production[p,t]) <= capacity[k] for each machine k and period t","inventory[p,t] <= max_inventory_per_product for each product p and period t","sales[p,t] <= sales_limit[p,t] for each product p and period t","inventory[p,4] = target_inventory_end for each product p"],"objective":"maximize sum_{p,t}(profit_per_unit[p] * sales[p,t] - holding_cost_per_unit * inventory[p,t])"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = range(3)
    periods = range(5)
    machines = ("grinder", "drill", "borer")

    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    capacities = {
        "grinder": params["grinder_capacity"],
        "drill": params["drill_capacity"],
        "borer": params["borer_capacity"],
    }
    machine_hours = {
        0: params["machine_hours_product0"],
        1: params["machine_hours_product1"],
        2: params["machine_hours_product2"],
    }
    max_inventory_per_product = params["max_inventory_per_product"]
    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
        2: params["sales_limit_product2"],
    }
    target_inventory_end = params["target_inventory_end"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products, ordered=True)
    model.periods = pyo.Set(initialize=periods, ordered=True)
    model.machines = pyo.Set(initialize=machines, ordered=True)

    model.unit_profit = pyo.Param(
        model.products,
        initialize={product: profit_per_unit[product] for product in products},
    )
    model.holding_cost = pyo.Param(initialize=holding_cost_per_unit)
    model.capacity = pyo.Param(model.machines, initialize=capacities)
    model.hours_required = pyo.Param(
        model.products,
        model.machines,
        initialize={
            (product, machine): machine_hours[product][machine_index]
            for product in products
            for machine_index, machine in enumerate(machines)
        },
    )
    model.inventory_limit = pyo.Param(initialize=max_inventory_per_product)
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in products
            for period in periods
        },
    )
    model.terminal_inventory = pyo.Param(initialize=target_inventory_end)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(factory, product):
        return (
            factory.production[product, 0]
            == factory.sales[product, 0] + factory.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(factory, product, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            factory.inventory[product, period - 1]
            + factory.production[product, period]
            == factory.sales[product, period]
            + factory.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(factory, machine, period):
        return (
            sum(
                factory.hours_required[product, machine]
                * factory.production[product, period]
                for product in factory.products
            )
            <= factory.capacity[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def inventory_limit_rule(factory, product, period):
        return (
            factory.inventory[product, period] <= factory.inventory_limit
        )

    model.inventory_bound = pyo.Constraint(
        model.products, model.periods, rule=inventory_limit_rule
    )

    def sales_limit_rule(factory, product, period):
        return (
            factory.sales[product, period]
            <= factory.sales_limit[product, period]
        )

    model.sales_bound = pyo.Constraint(
        model.products, model.periods, rule=sales_limit_rule
    )

    def terminal_inventory_rule(factory, product):
        return (
            factory.inventory[product, 4] == factory.terminal_inventory
        )

    model.target_inventory = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}