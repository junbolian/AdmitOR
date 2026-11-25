# IR: {"sets":{"crops":"0..24"},"params":{"capacity":"params['capacity']","crop_value[c]":"params['values'][c]","crop_weight[c]":"params['weights'][c]"},"variables":{"selected[c]":"Binary"},"constraints":["sum(crop_weight[c]*selected[c] for c in crops) <= capacity"],"objective":"maximize sum(crop_value[c]*selected[c] for c in crops)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.crops = pyo.RangeSet(0, 24)

    model.capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.crop_value = pyo.Param(
        model.crops,
        initialize={crop: params["values"][crop] for crop in range(25)},
        within=pyo.Reals,
    )
    model.crop_weight = pyo.Param(
        model.crops,
        initialize={crop: params["weights"][crop] for crop in range(25)},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.crops, domain=pyo.Binary)

    model.storage_limit = pyo.Constraint(
        expr=sum(
            model.crop_weight[crop] * model.selected[crop]
            for crop in model.crops
        ) <= model.capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.crop_value[crop] * model.selected[crop]
            for crop in model.crops
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