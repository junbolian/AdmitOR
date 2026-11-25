# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4,5],"K":["grinders","drills","borers"]},"params":{"profit_per_unit":"P","holding_cost":"scalar","machine_capacity":"K; input order grinders,drills,borers","time_grinders":"P","time_drills":"P","time_borers":"P","inventory_limit":"P; scalar input broadcast to all products","sales_limit":"P x T","target_inventory":"P; scalar input broadcast to all products"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t>0","sum_p processing_time[k,p]*production[p,t] <= machine_capacity[k]","inventory[p,t] <= inventory_limit[p]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = target_inventory[p]"],"objective":"maximize sum_(p,t) (profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t])"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 5)
    machine_types = ("grinders", "drills", "borers")
    model.K = pyo.Set(initialize=machine_types, ordered=True)

    def product_value(data, product):
        return data if isinstance(data, Number) else data[product]

    model.profit_per_unit = pyo.Param(
        model.P,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.P
        },
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])

    model.machine_capacity = pyo.Param(
        model.K,
        initialize={
            kind: params["machine_capacity"][position]
            for position, kind in enumerate(machine_types)
        },
    )

    time_inputs = {
        "grinders": params["time_grinders"],
        "drills": params["time_drills"],
        "borers": params["time_borers"],
    }
    model.processing_time = pyo.Param(
        model.K,
        model.P,
        initialize={
            (kind, product): time_inputs[kind][product]
            for kind in machine_types
            for product in model.P
        },
    )
    model.inventory_limit = pyo.Param(
        model.P,
        initialize={
            product: product_value(params["inventory_limit"], product)
            for product in model.P
        },
    )
    model.sales_limit = pyo.Param(
        model.P,
        model.T,
        initialize={
            (product, period): params["sales_limit"][product][period]
            for product in model.P
            for period in model.T
        },
    )
    model.target_inventory = pyo.Param(
        model.P,
        initialize={
            product: product_value(params["target_inventory"], product)
            for product in model.P
        },
    )

    model.production = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def balance_rule(mod, product, period):
        if period == 0:
            return (
                mod.production[product, period]
                == mod.sales[product, period] + mod.inventory[product, period]
            )
        return (
            mod.inventory[product, period - 1] + mod.production[product, period]
            == mod.sales[product, period] + mod.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.P, model.T, rule=balance_rule
    )

    def capacity_rule(mod, kind, period):
        return (
            sum(
                mod.processing_time[kind, product]
                * mod.production[product, period]
                for product in mod.P
            )
            <= mod.machine_capacity[kind]
        )

    model.capacity_constraints = pyo.Constraint(
        model.K, model.T, rule=capacity_rule
    )
    model.inventory_bounds = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mod, product, period: (
            mod.inventory[product, period] <= mod.inventory_limit[product]
        ),
    )
    model.sales_bounds = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mod, product, period: (
            mod.sales[product, period] <= mod.sales_limit[product, period]
        ),
    )
    model.terminal_inventory = pyo.Constraint(
        model.P,
        rule=lambda mod, product: (
            mod.inventory[product, 5] == mod.target_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.P
            for period in model.T
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}