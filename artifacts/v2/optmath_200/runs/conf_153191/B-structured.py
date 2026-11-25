# IR: {"sets":{"I":"0..25"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i]","weights[i]":"params['weights'][i]"},"variables":{"x[i]":"binary for i in I"},"constraints":["sum(weights[i]*x[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 25)

    model.capacity = pyo.Param(initialize=params["capacity"])
    model.item_values = pyo.Param(
        model.item_set,
        initialize={i: params["values"][i] for i in model.item_set},
    )
    model.item_weights = pyo.Param(
        model.item_set,
        initialize={i: params["weights"][i] for i in model.item_set},
    )

    model.x = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.x[i] for i in model.item_set
        ) <= model.capacity
    )
    model.total_value = pyo.Objective(
        expr=sum(model.item_values[i] * model.x[i] for i in model.item_set),
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