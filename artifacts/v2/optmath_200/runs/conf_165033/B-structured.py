# IR: {"sets":{"I":"0..11"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i]","weights[i]":"params['weights'][i]"},"variables":{"selected[i]":"Binary, i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 11)

    model.vehicle_capacity = pyo.Param(initialize=capacity)
    model.item_values = pyo.Param(
        model.item_indices,
        initialize={i: values[i] for i in model.item_indices},
    )
    model.item_weights = pyo.Param(
        model.item_indices,
        initialize={i: weights[i] for i in model.item_indices},
    )

    model.selected = pyo.Var(model.item_indices, domain=pyo.Binary)

    model.capacity_constraint = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_indices
        ) <= model.vehicle_capacity
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
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}