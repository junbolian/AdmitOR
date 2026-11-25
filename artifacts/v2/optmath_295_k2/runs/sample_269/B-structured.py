# IR: {"sets":{"I":"0..14"},"params":{"profit":"real[I]","resource_consumption":"real[I]","total_resource":"real","capacity":"real[I]"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in I) <= total_resource","quantity[i] <= capacity[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 14)

    model.profit = pyo.Param(
        model.item_set,
        initialize={i: params["profit"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={
            i: params["resource_consumption"][i] for i in model.item_set
        },
        within=pyo.Reals,
    )
    model.total_resource = pyo.Param(
        initialize=params["total_resource"],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.item_set,
        initialize={i: params["capacity"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.quantity[i]
            for i in model.item_set
        ) <= model.total_resource
    )

    def capacity_rule(instance, i):
        return instance.quantity[i] <= instance.capacity[i]

    model.capacity_limit = pyo.Constraint(
        model.item_set, rule=capacity_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}