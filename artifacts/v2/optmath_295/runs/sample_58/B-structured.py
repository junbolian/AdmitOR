# IR: {"sets":{"I":"0..92"},"params":{"capacity":"scalar from params['capacity']","values":"I-indexed from params['values']","weights":"I-indexed from params['weights']"},"variables":{"selected[i]":"Binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_set = pyo.RangeSet(0, 92)

    model.vehicle_capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )
    model.item_value = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["values"][i],
        within=pyo.Reals,
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["weights"][i],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[i] * model.selected[i]
            for i in model.item_set
        ) <= model.vehicle_capacity
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.item_value[i] * model.selected[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}