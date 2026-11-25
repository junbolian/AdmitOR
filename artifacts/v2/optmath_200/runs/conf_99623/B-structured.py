# IR: {"sets":{"I":"0..41"},"params":{"profit_per_unit":"real[I]","resource_consumption":"real[I]","resource_capacity":"real","production_limit":"real[I]"},"decision_variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in I) <= resource_capacity","quantity[i] <= production_limit[i] for i in I"],"objective":"maximize sum(profit_per_unit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 41)

    model.profit_per_unit = pyo.Param(
        model.I,
        initialize={i: params["profit_per_unit"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.I,
        initialize={i: params["resource_consumption"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.I,
        initialize={i: params["production_limit"][i] for i in model.I},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.quantity[i]
            for i in model.I
        ) <= model.resource_capacity
    )

    def production_limit_rule(block, i):
        return block.quantity[i] <= block.production_limit[i]

    model.production_constraints = pyo.Constraint(
        model.I, rule=production_limit_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.quantity[i]
            for i in model.I
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