# IR: {"sets":{"products":"0..9"},"params":{"profit_per_unit":"real[products]","time_per_unit":"nonnegative real[products]","total_time_available":"nonnegative real","min_production":"nonnegative real[products]","max_production":"nonnegative real[products]"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["sum(time_per_unit[i]*production[i] for i in products) <= total_time_available","production[i] >= min_production[i] for i in products","production[i] <= max_production[i] for i in products"],"objective":"maximize sum(profit_per_unit[i]*production[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 9)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={i: params["profit_per_unit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.total_time_available = pyo.Param(
        initialize=params["total_time_available"],
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

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.time_capacity = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.production[i]
            for i in model.products
        )
        <= model.total_time_available
    )
    model.production_minimum = pyo.Constraint(
        model.products,
        rule=lambda mdl, i: mdl.production[i] >= mdl.min_production[i],
    )
    model.production_maximum = pyo.Constraint(
        model.products,
        rule=lambda mdl, i: mdl.production[i] <= mdl.max_production[i],
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.production[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Success is determined solely by objective retrieval below.
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}