# IR: {"sets":{"item_indices":"0..81"},"params":{"capacity":"params['capacity']","item_values[i]":"params['values'][i]","item_weights[i]":"params['weights'][i]"},"variables":{"selected[i]":"binary, i in item_indices"},"constraints":["sum(item_weights[i] * selected[i] for i in item_indices) <= capacity"],"objective":"maximize sum(item_values[i] * selected[i] for i in item_indices)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 81)

    model.capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.item_values = pyo.Param(
        model.item_indices,
        initialize={
            i: params["values"][i] for i in model.item_indices
        },
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_indices,
        initialize={
            i: params["weights"][i] for i in model.item_indices
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(
        model.item_indices,
        domain=pyo.Binary,
    )

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_indices
        ) <= model.capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.selected[i]
            for i in model.item_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective_value"}

    return {"objective": obj_val, "status": "optimal"}