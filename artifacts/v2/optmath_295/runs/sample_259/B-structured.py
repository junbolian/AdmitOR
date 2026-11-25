# IR: {"sets":{"products":"0..10"},"params":{"profit":"profit[i]","time_per_unit":"time_per_unit[i]","time_capacity":"scalar","min_production":"min_production[i]","max_production":"max_production[i]"},"variables":{"quantity[i]":"nonnegative continuous"},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= time_capacity","quantity[i] >= min_production[i] for each i","quantity[i] <= max_production[i] for each i"],"objective":"maximize sum(profit[i]*quantity[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize=lambda mdl, i: profit[i],
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, i: time_per_unit[i],
    )
    model.time_capacity = pyo.Param(initialize=time_capacity)
    model.min_production = pyo.Param(
        model.products,
        initialize=lambda mdl, i: min_production[i],
    )
    model.max_production = pyo.Param(
        model.products,
        initialize=lambda mdl, i: max_production[i],
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.time_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        )
        <= model.time_capacity
    )
    model.production_minimum = pyo.Constraint(
        model.products,
        rule=lambda mdl, i: mdl.quantity[i] >= mdl.min_production[i],
    )
    model.production_maximum = pyo.Constraint(
        model.products,
        rule=lambda mdl, i: mdl.quantity[i] <= mdl.max_production[i],
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}