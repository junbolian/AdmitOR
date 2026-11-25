# IR: {"sets":{"item_set":"0..92"},"params":{"capacity":"params['capacity']","item_values[i]":"params['item_values'][i]","item_weights[i]":"params['item_weights'][i]"},"decision_variables":{"selected[i]":{"index":"item_set","type":"binary"}},"constraints":["sum(item_weights[i]*selected[i] for i in item_set) <= capacity"],"objective":{"sense":"maximize","expression":"sum(item_values[i]*selected[i] for i in item_set)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 92)

    model.capacity = pyo.Param(initialize=params["capacity"])
    model.item_values = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["item_values"][i],
    )
    model.item_weights = pyo.Param(
        model.item_set,
        initialize=lambda mdl, i: params["item_weights"][i],
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.selected[i]
            for i in model.item_set
        ) <= model.capacity
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.selected[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Objective retrieval below determines whether a solution is available.
        pass

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}