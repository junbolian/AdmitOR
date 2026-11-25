# IR: {"sets":{"I":"0..46"},"params":{"profit":"real[I]","resource_usage":"real[I]","capacity":"real[I]","resource_budget":"real"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_usage[i]*quantity[i] for i in I) <= resource_budget","quantity[i] <= capacity[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 46)

    model.profit = pyo.Param(
        model.I,
        initialize={i: params["profit"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_usage = pyo.Param(
        model.I,
        initialize={i: params["resource_usage"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        initialize={i: params["capacity"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_budget = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_usage[i] * model.quantity[i] for i in model.I
        ) <= model.resource_budget
    )

    def capacity_rule(mdl, i):
        return mdl.quantity[i] <= mdl.capacity[i]

    model.production_limits = pyo.Constraint(model.I, rule=capacity_rule)

    model.total_profit = pyo.Objective(
        expr=sum(model.profit[i] * model.quantity[i] for i in model.I),
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