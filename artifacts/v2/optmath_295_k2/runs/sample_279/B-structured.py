# IR: {"sets":{"I":"0..81"},"params":{"capacity":"scalar","values":"indexed by I","weights":"indexed by I"},"variables":{"x[i]":"binary for i in I"},"constraints":["sum(weights[i]*x[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 81)

    model.vehicle_capacity = pyo.Param(initialize=capacity)
    model.item_value = pyo.Param(
        model.item_set,
        initialize={i: values[i] for i in model.item_set},
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize={i: weights[i] for i in model.item_set},
    )

    model.x = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(model.item_weight[i] * model.x[i] for i in model.item_set)
        <= model.vehicle_capacity
    )
    model.total_value = pyo.Objective(
        expr=sum(model.item_value[i] * model.x[i] for i in model.item_set),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}