# IR: {"sets":{"I":"{0,...,80}"},"params":{"capacity":"real scalar from params['capacity']","values":"real array indexed by I from params['values']","weights":"real array indexed by I from params['weights']"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 80)

    model.truck_capacity = pyo.Param(
        initialize=capacity,
        within=pyo.Reals,
    )
    model.item_values = pyo.Param(
        model.item_set,
        initialize={i: values[i] for i in range(81)},
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_set,
        initialize={i: weights[i] for i in range(81)},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_set
        ) <= model.truck_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.selected[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}