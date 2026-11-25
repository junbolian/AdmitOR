# IR: {"sets":{"I":"0..80"},"params":{"capacity":"scalar from params['capacity']","values":"indexed by I from params['values']","weights":"indexed by I from params['weights']"},"variables":{"selected[i]":"Binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

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
    model.item_value = pyo.Param(
        model.item_set,
        initialize={i: values[i] for i in range(81)},
        within=pyo.Reals,
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize={i: weights[i] for i in range(81)},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[i] * model.selected[i]
            for i in model.item_set
        ) <= model.truck_capacity
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}