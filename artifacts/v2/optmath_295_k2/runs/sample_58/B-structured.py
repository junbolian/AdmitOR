# IR: {"sets":{"item_ids":"0..92"},"params":{"capacity":"params['capacity']","item_values[i]":"params['item_values'][i]","item_weights[i]":"params['item_weights'][i]"},"variables":{"selected[i]":"Binary"},"constraints":["sum(item_weights[i]*selected[i] for i in item_ids) <= capacity"],"objective":"maximize sum(item_values[i]*selected[i] for i in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.RangeSet(0, 92)

    model.capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.item_values = pyo.Param(
        model.item_ids,
        initialize={
            i: params["item_values"][i]
            for i in model.item_ids
        },
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={
            i: params["item_weights"][i]
            for i in model.item_ids
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(
        model.item_ids,
        domain=pyo.Binary,
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_ids
        ) <= model.capacity
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.selected[i]
            for i in model.item_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}