# IR: {"sets":{"item_set":"0..19"},"params":{"profit":"real[item_set]","consumption":"real[item_set]","capacity":"real","upper_limit":"real[item_set]"},"variables":{"quantity":"nonnegative continuous[item_set]"},"constraints":["sum(consumption[i]*quantity[i] for i in item_set) <= capacity","quantity[i] <= upper_limit[i] for i in item_set"],"objective":"maximize sum(profit[i]*quantity[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 19)

    model.profit = pyo.Param(
        model.item_set,
        initialize={i: params["profit"][i] for i in range(20)},
        within=pyo.Reals,
    )
    model.consumption = pyo.Param(
        model.item_set,
        initialize={i: params["consumption"][i] for i in range(20)},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.upper_limit = pyo.Param(
        model.item_set,
        initialize={i: params["upper_limit"][i] for i in range(20)},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_capacity = pyo.Constraint(
        expr=sum(
            model.consumption[i] * model.quantity[i]
            for i in model.item_set
        ) <= model.capacity
    )

    def production_limit_rule(mdl, i):
        return mdl.quantity[i] <= mdl.upper_limit[i]

    model.production_limit = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}