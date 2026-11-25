# IR: {"sets":{"crops":"0..24"},"params":{"capacity":"real, from params['capacity']","crop_values":"real[crops], from params['values']","crop_weights":"real[crops], from params['weights']"},"variables":{"selected":"binary[crops]"},"constraints":["sum(crop_weights[i]*selected[i] for i in crops) <= capacity"],"objective":"maximize sum(crop_values[i]*selected[i] for i in crops)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.crops = pyo.RangeSet(0, 24)

    model.capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.crop_values = pyo.Param(
        model.crops,
        initialize={i: params["values"][i] for i in model.crops},
        within=pyo.Reals,
    )
    model.crop_weights = pyo.Param(
        model.crops,
        initialize={i: params["weights"][i] for i in model.crops},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.crops, domain=pyo.Binary)

    model.storage_limit = pyo.Constraint(
        expr=sum(
            model.crop_weights[i] * model.selected[i]
            for i in model.crops
        ) <= model.capacity
    )

    model.harvest_value = pyo.Objective(
        expr=sum(
            model.crop_values[i] * model.selected[i]
            for i in model.crops
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.harvest_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}