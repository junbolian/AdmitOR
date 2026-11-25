# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit[p]":"scalar(params[f'profit_product_{p}'])","holding_cost":"scalar(params['holding_cost'])","capacity[k]":"scalar(params[f'{k}_capacity'])","max_inventory":"scalar(params['max_inventory'])","max_sales[t,p]":"scalar(params[f'max_sales_period_{t}_product_{p}'])","final_inventory_target":"scalar(params['final_inventory_target'])","processing_time[k,p]":"scalar(params[f'time_{k}_product_{p}'])"},"variables":{"production[t,p]":"nonnegative continuous","sales[t,p]":"nonnegative continuous","inventory[t,p]":"nonnegative continuous"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p] for each p","inventory[t-1,p] + production[t,p] = sales[t,p] + inventory[t,p] for each t>0,p","sum_p processing_time[k,p]*production[t,p] <= (0 if k='borer' and t=2 else capacity[k]) for each t,k","sales[t,p] <= max_sales[t,p] for each t,p","inventory[t,p] <= max_inventory for each t,p","inventory[3,p] = final_inventory_target for each p"],"objective":"maximize sum_{t,p}(profit[p]*sales[t,p] - holding_cost*inventory[t,p])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _scalar(value):
    """Convert a scalar or singleton-list-wrapped scalar to a float."""
    while isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise ValueError("Each parameter must contain exactly one numeric value.")
        value = value[0]
    return float(value)


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.machines = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            product: _scalar(params[f"profit_product_{product}"])
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.inventory_holding_cost = pyo.Param(
        initialize=_scalar(params["holding_cost"]),
        within=pyo.Reals,
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize={
            machine: _scalar(params[f"{machine}_capacity"])
            for machine in model.machines
        },
        within=pyo.Reals,
    )
    model.inventory_limit = pyo.Param(
        initialize=_scalar(params["max_inventory"]),
        within=pyo.Reals,
    )
    model.sales_limit = pyo.Param(
        model.periods,
        model.products,
        initialize={
            (period, product): _scalar(
                params[f"max_sales_period_{period}_product_{product}"]
            )
            for period in model.periods
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.terminal_inventory_target = pyo.Param(
        initialize=_scalar(params["final_inventory_target"]),
        within=pyo.Reals,
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product): _scalar(
                params[f"time_{machine}_product_{product}"]
            )
            for machine in model.machines
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.periods, model.products, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(model, period, product):
        if period == 0:
            return (
                model.production[period, product]
                == model.sales[period, product]
                + model.inventory[period, product]
            )
        return (
            model.inventory[period - 1, product]
            + model.production[period, product]
            == model.sales[period, product]
            + model.inventory[period, product]
        )

    model.inventory_balance = pyo.Constraint(
        model.periods, model.products, rule=inventory_balance_rule
    )

    def machine_capacity_rule(model, period, machine):
        available_capacity = (
            0
            if machine == "borer" and period == 2
            else model.machine_capacity[machine]
        )
        return (
            sum(
                model.processing_time[machine, product]
                * model.production[period, product]
                for product in model.products
            )
            <= available_capacity
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.periods, model.machines, rule=machine_capacity_rule
    )

    def sales_limit_rule(model, period, product):
        return model.sales[period, product] <= model.sales_limit[period, product]

    model.sales_limit_constraints = pyo.Constraint(
        model.periods, model.products, rule=sales_limit_rule
    )

    def inventory_limit_rule(model, period, product):
        return model.inventory[period, product] <= model.inventory_limit

    model.inventory_limit_constraints = pyo.Constraint(
        model.periods, model.products, rule=inventory_limit_rule
    )

    def terminal_inventory_rule(model, product):
        return model.inventory[3, product] == model.terminal_inventory_target

    model.terminal_inventory_constraints = pyo.Constraint(
        model.products, rule=terminal_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[period, product]
            - model.inventory_holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}