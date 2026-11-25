# IR: {"sets":{"I":"0..11"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i]","weights[i]":"params['weights'][i]"},"variables":{"select[i]":"Binary for i in I"},"constraints":["sum(weights[i]*select[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*select[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 11)

    model.capacity = pyo.Param(initialize=params["capacity"])
    model.item_value = pyo.Param(
        model.item_set,
        initialize={i: params["values"][i] for i in model.item_set},
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize={i: params["weights"][i] for i in model.item_set},
    )

    model.select = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[i] * model.select[i] for i in model.item_set
        ) <= model.capacity
    )
    model.total_revenue = pyo.Objective(
        expr=sum(
            model.item_value[i] * model.select[i] for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}