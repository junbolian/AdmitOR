# IR: {"sets":{"item_set":"{0,...,80}"},"params":{"capacity_limit":"real scalar from params['capacity']","item_value":"real array indexed by item_set from params['values']","item_weight":"real array indexed by item_set from params['weights']"},"variables":{"selected[i]":"binary for i in item_set"},"constraints":["sum(item_weight[i]*selected[i] for i in item_set) <= capacity_limit"],"objective":"maximize sum(item_value[i]*selected[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 80)

    model.capacity_limit = pyo.Param(
        initialize=capacity,
        within=pyo.Reals,
    )
    model.item_value = pyo.Param(
        model.item_set,
        initialize={i: values[i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize={i: weights[i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[i] * model.selected[i]
            for i in model.item_set
        ) <= model.capacity_limit
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_value[i] * model.selected[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}