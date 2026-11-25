# IR: {"sets":{"I":"0..92"},"params":{"capacity":"real scalar from params['capacity']","values":"real[I] from params['values']","weights":"real[I] from params['weights']"},"variables":{"x[i]":"binary for i in I"},"constraints":["sum(weights[i]*x[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 92)

    model.vehicle_capacity = pyo.Param(
        initialize=capacity,
        within=pyo.Reals,
    )
    model.item_values = pyo.Param(
        model.item_indices,
        initialize={i: values[i] for i in range(93)},
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_indices,
        initialize={i: weights[i] for i in range(93)},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.item_indices, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.x[i]
            for i in model.item_indices
        ) <= model.vehicle_capacity
    )
    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.x[i]
            for i in model.item_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}