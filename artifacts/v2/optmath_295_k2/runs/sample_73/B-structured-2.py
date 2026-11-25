# IR: {"sets":{"I":"item_0 through item_26"},"params":{"capacity":"scalar from params['capacity']","value":"I-indexed from params['value']","weight":"I-indexed from params['weight']"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weight[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(value[i]*selected[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the knapsack using sequences or item-keyed mappings as input."""
    item_labels = tuple(f"item_{idx}" for idx in range(27))
    capacity = params["capacity"]
    values = params["value"]
    weights = params["weight"]

    def item_data(data):
        if isinstance(data, Mapping):
            if all(item in data for item in item_labels):
                return {item: data[item] for item in item_labels}
            return {item: data[idx] for idx, item in enumerate(item_labels)}
        if len(data) != len(item_labels):
            raise ValueError("Expected exactly 27 item entries.")
        return {item: data[idx] for idx, item in enumerate(item_labels)}

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)
    model.capacity = pyo.Param(initialize=capacity, within=pyo.Reals)
    model.item_value = pyo.Param(
        model.item_set, initialize=item_data(values), within=pyo.Reals
    )
    model.item_weight = pyo.Param(
        model.item_set, initialize=item_data(weights), within=pyo.Reals
    )
    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[item] * model.selected[item]
            for item in model.item_set
        ) <= model.capacity
    )
    model.total_value = pyo.Objective(
        expr=sum(
            model.item_value[item] * model.selected[item]
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