# IR: {"sets":{"I":"0..32"},"params":{"values":"values[i] for i in I","weights":"weights[i] for i in I","capacity":"maximum total weight"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.item_ids = pyo.RangeSet(0, 32)

    model.item_values = pyo.Param(
        model.item_ids,
        initialize={i: values[i] for i in model.item_ids},
    )
    model.item_weights = pyo.Param(
        model.item_ids,
        initialize={i: weights[i] for i in model.item_ids},
    )
    model.weight_capacity = pyo.Param(initialize=capacity)

    model.selected = pyo.Var(model.item_ids, domain=pyo.Binary)

    model.capacity_constraint = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_ids
        ) <= model.weight_capacity
    )

    model.total_value = pyo.Objective(
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
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}