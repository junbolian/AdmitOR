# IR: {"sets":{"item_ids":"item_0 through item_26"},"params":{"item_values[item]":"params['values'][item]","item_weights[item]":"params['weights'][item]","capacity_limit":"params['capacity']"},"variables":{"selected[item]":"binary"},"constraints":["sum(item_weights[item] * selected[item] for item in item_ids) <= capacity_limit"],"objective":"maximize sum(item_values[item] * selected[item] for item in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.Set(
        initialize=[f"item_{item_index}" for item_index in range(27)],
        ordered=True,
    )

    model.item_values = pyo.Param(
        model.item_ids,
        initialize={item: params["values"][item] for item in model.item_ids},
        within=pyo.Reals,
    )

    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={item: params["weights"][item] for item in model.item_ids},
        within=pyo.Reals,
    )

    model.capacity_limit = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_ids, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[item] * model.selected[item]
            for item in model.item_ids
        )
        <= model.capacity_limit
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[item] * model.selected[item]
            for item in model.item_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}