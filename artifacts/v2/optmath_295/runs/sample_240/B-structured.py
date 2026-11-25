# IR: {"sets":{"item_set":"item_0 through item_26"},"params":{"item_values":"real mapping from params['values'], indexed by item_set","item_weights":"real mapping from params['weights'], indexed by item_set","weight_capacity":"real scalar from params['capacity']"},"decision_variables":{"selected[item]":"binary for each item in item_set"},"constraints":["sum(item_weights[item] * selected[item] for item in item_set) <= weight_capacity"],"objective":"maximize sum(item_values[item] * selected[item] for item in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_labels = [f"item_{item_index}" for item_index in range(27)]
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

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
    model.weight_capacity = pyo.Param(
        initialize=capacity,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.capacity_constraint = pyo.Constraint(
        expr=sum(
            model.item_weights[item] * model.selected[item]
            for item in model.item_set
        ) <= model.weight_capacity
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
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}