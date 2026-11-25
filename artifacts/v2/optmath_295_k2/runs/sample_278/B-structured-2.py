# IR: {"sets":{"item_ids":"item_0 through item_31"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i]","weights[i]":"params['weights'][i]"},"decision_variables":{"selected[i]":"binary for i in item_ids"},"constraints":["sum(weights[i]*selected[i] for i in item_ids) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_ids = [f"item_{i}" for i in range(32)]

    model = pyo.ConcreteModel()
    model.item_ids = pyo.Set(initialize=item_ids, ordered=True)

    model.capacity = pyo.Param(initialize=params["capacity"])
    model.item_values = pyo.Param(
        model.item_ids,
        initialize={item: params["values"][item] for item in item_ids},
    )
    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={item: params["weights"][item] for item in item_ids},
    )

    model.selected = pyo.Var(model.item_ids, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[item] * model.selected[item]
            for item in model.item_ids
        ) <= model.capacity
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}