# IR: {"sets":{"products":[0,1,2],"periods":[0,1,2,3],"machines":["grinder","drill","borer"]},"params":{"profit[p]":"numeric(params['profit_product_'+str(p)])","holding_cost":"numeric(params['holding_cost'])","capacity[k,t]":"numeric(params[k+'_capacity']) if scalar or singleton; otherwise numeric(params[k+'_capacity'][t]) for a four-period sequence","max_inventory":"numeric(params['max_inventory'])","max_sales[t,p]":"numeric(params['max_sales_period_'+str(t)+'_product_'+str(p)])","final_inventory_target":"numeric(params['final_inventory_target'])","processing_time[k,p]":"numeric(params['time_'+k+'_product_'+str(p)])"},"variables":{"production[t,p]":"NonNegativeReals","sales[t,p]":"NonNegativeReals","inventory[t,p]":"NonNegativeReals"},"constraints":["production[0,p] = sales[0,p] + inventory[0,p] for each p","inventory[t-1,p] + production[t,p] = sales[t,p] + inventory[t,p] for each t>0,p","sum(processing_time[k,p]*production[t,p] for p) <= (0 if k='borer' and t=2 else capacity[k,t]) for each k,t","sales[t,p] <= max_sales[t,p] for each t,p","inventory[t,p] <= max_inventory for each t,p","inventory[3,p] = final_inventory_target for each p"],"objective":"maximize sum(profit[p]*sales[t,p] - holding_cost*inventory[t,p] for t,p)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def _numeric(value):
    """Convert a scalar or nested singleton list/tuple to a number."""
    while isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise ValueError("Expected a numeric scalar or singleton sequence.")
        value = value[0]
    return float(value)


def _period_capacity(value, period, period_count):
    """Accept scalar, singleton, or one numeric capacity per period."""
    while isinstance(value, (list, tuple)):
        if len(value) == 1:
            value = value[0]
        elif len(value) == period_count:
            return _numeric(value[period])
        else:
            raise ValueError(
                "Capacity must be a scalar, singleton sequence, "
                "or sequence with one entry per period."
            )
    return _numeric(value)


def solve(params):
    model = pyo.ConcreteModel()

    products = tuple(range(3))
    periods = tuple(range(4))
    machines = ("grinder", "drill", "borer")

    model.products = pyo.Set(initialize=products, ordered=True)
    model.periods = pyo.Set(initialize=periods, ordered=True)
    model.machines = pyo.Set(initialize=machines, ordered=True)

    model.profit = pyo.Param(
        model.products,
        initialize={
            product: _numeric(params[f"profit_product_{product}"])
            for product in products
        },
    )
    model.holding_cost = pyo.Param(
        initialize=_numeric(params["holding_cost"])
    )
    model.capacity_hours = pyo.Param(
        model.machines,
        model.periods,
        initialize={
            (machine, period): _period_capacity(
                params[f"{machine}_capacity"], period, len(periods)
            )
            for machine in machines
            for period in periods
        },
    )
    model.max_inventory = pyo.Param(
        initialize=_numeric(params["max_inventory"])
    )
    model.max_sales = pyo.Param(
        model.periods,
        model.products,
        initialize={
            (period, product): _numeric(
                params[f"max_sales_period_{period}_product_{product}"]
            )
            for period in periods
            for product in products
        },
    )
    model.final_inventory_target = pyo.Param(
        initialize=_numeric(params["final_inventory_target"])
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize={
            (machine, product): _numeric(
                params[f"time_{machine}_product_{product}"]
            )
            for machine in machines
            for product in products
        },
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

    def machine_capacity_rule(model, machine, period):
        available_hours = (
            0
            if machine == "borer" and period == 2
            else model.capacity_hours[machine, period]
        )
        return (
            sum(
                model.processing_time[machine, product]
                * model.production[period, product]
                for product in model.products
            )
            <= available_hours
        )

    model.machine_capacity_limits = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
    )

    def sales_limit_rule(model, period, product):
        return model.sales[period, product] <= model.max_sales[period, product]

    model.sales_limits = pyo.Constraint(
        model.periods, model.products, rule=sales_limit_rule
    )

    def inventory_limit_rule(model, period, product):
        return model.inventory[period, product] <= model.max_inventory

    model.inventory_limits = pyo.Constraint(
        model.periods, model.products, rule=inventory_limit_rule
    )

    def final_inventory_rule(model, product):
        return model.inventory[3, product] == model.final_inventory_target

    model.final_inventory_requirement = pyo.Constraint(
        model.products, rule=final_inventory_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[period, product]
            - model.holding_cost * model.inventory[period, product]
            for period in model.periods
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrievability below.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}