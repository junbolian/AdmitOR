# IR: {"sets":{"I":"item_0 through item_26"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i] for i in I","weights[i]":"params['weights'][i] for i in I"},"decision_variables":{"selected[i]":"Binary for i in I"},"constraints":["sum(weights[i] * selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i] * selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_labels = [f"item_{idx}" for idx in range(27)]
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

    model.capacity = pyo.Param(initialize=capacity, within=pyo.Reals)
    model.item_values = pyo.Param(
        model.item_set,
        initialize={item: values[item] for item in item_labels},
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_set,
        initialize={item: weights[item] for item in item_labels},
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.item_weights[item] * model.selected[item]
            for item in model.item_set
        )
        <= model.capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[item] * model.selected[item]
            for item in model.item_set
        ),
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