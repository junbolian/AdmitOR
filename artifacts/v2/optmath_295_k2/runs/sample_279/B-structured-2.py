# IR: {"sets":{"I":"0..81"},"params":{"capacity":"scalar","values":"indexed by I","weights":"indexed by I"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 81)

    model.vehicle_capacity = pyo.Param(initialize=capacity)
    model.item_values = pyo.Param(
        model.I, initialize={i: values[i] for i in model.I}
    )
    model.item_weights = pyo.Param(
        model.I, initialize={i: weights[i] for i in model.I}
    )

    model.selected = pyo.Var(model.I, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(model.item_weights[i] * model.selected[i] for i in model.I)
        <= model.vehicle_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(model.item_values[i] * model.selected[i] for i in model.I),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}