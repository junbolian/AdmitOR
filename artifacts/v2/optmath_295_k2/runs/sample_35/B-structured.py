# IR: {"sets":{"I":"0..10"},"params":{"profit":"real[I]","resource_consumption":"real[I]","resource_capacity":"real","production_capacity":"real[I]"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in I) <= resource_capacity","quantity[i] <= production_capacity[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.item_indices,
        initialize={i: params["profit"][i] for i in model.item_indices},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_indices,
        initialize={
            i: params["resource_consumption"][i]
            for i in model.item_indices
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_capacity = pyo.Param(
        model.item_indices,
        initialize={
            i: params["production_capacity"][i]
            for i in model.item_indices
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_indices,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.quantity[i]
            for i in model.item_indices
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.quantity[i] <= instance.production_capacity[i]

    model.production_limit = pyo.Constraint(
        model.item_indices,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.item_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "no_objective_value"}

    return {"objective": obj_val, "status": "optimal"}