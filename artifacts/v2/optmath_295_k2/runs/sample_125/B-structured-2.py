# IR: {"sets":{"products":"0..11"},"params":{"profit":"real[products]","time_per_unit":"nonnegative real[products]","capacity_hours":"nonnegative real","min_production":"nonnegative real[products]","max_production":"nonnegative real[products]"},"variables":{"quantity":"nonnegative continuous[products]"},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= capacity_hours","quantity[i] >= min_production[i] for each i in products","quantity[i] <= max_production[i] for each i in products"],"objective":"maximize sum(profit[i]*quantity[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 11)

    model.profit = pyo.Param(
        model.products,
        initialize={i: params["profit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.capacity_hours = pyo.Param(
        initialize=params["capacity_hours"],
        within=pyo.NonNegativeReals,
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={i: params["min_production"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.products,
        initialize={i: params["max_production"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        ) <= model.capacity_hours
    )
    model.minimum_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, i: mdl.quantity[i] >= mdl.min_production[i],
    )
    model.maximum_requirement = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}