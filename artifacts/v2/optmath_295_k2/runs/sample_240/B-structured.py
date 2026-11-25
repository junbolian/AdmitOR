# IR: {"sets":{"item_set":"item_0 through item_26"},"params":{"item_values":"real, indexed by item_set, from params['values']","item_weights":"nonnegative real, indexed by item_set, from params['weights']","capacity_limit":"real, from params['capacity']"},"variables":{"selected[item]":"Binary"},"constraints":["sum(item_weights[item] * selected[item] for item in item_set) <= capacity_limit"],"objective":{"sense":"maximize","expression":"sum(item_values[item] * selected[item] for item in item_set)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(
        initialize=[f"item_{item_idx}" for item_idx in range(27)],
        ordered=True,
    )

    model.item_values = pyo.Param(
        model.item_set,
        initialize={
            item: params["values"][item]
            for item in model.item_set
        },
        within=pyo.Reals,
    )

    model.item_weights = pyo.Param(
        model.item_set,
        initialize={
            item: params["weights"][item]
            for item in model.item_set
        },
        within=pyo.NonNegativeReals,
    )

    model.capacity_limit = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_constraint = pyo.Constraint(
        expr=sum(
            model.item_weights[item] * model.selected[item]
            for item in model.item_set
        ) <= model.capacity_limit
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[item] * model.selected[item]
            for item in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}