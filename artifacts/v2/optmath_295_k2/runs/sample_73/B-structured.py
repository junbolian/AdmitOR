# IR: {"sets":{"item_set":"item_0 through item_26"},"params":{"capacity":"scalar real from params['capacity']","item_value":"item_set-indexed real from params['value']","item_weight":"item_set-indexed real from params['weight']"},"variables":{"selected[item]":"Binary for item in item_set"},"constraints":["weight_limit: sum(item_weight[item]*selected[item] for item in item_set) <= capacity"],"objective":"total_value: maximize sum(item_value[item]*selected[item] for item in item_set)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve a 27-item binary knapsack problem.

    Item values and weights may be sequences ordered item_0 through item_26,
    or mappings keyed by item labels or integer indices.
    """
    item_labels = tuple(f"item_{idx}" for idx in range(27))
    capacity = params["capacity"]
    values = params["value"]
    weights = params["weight"]

    def indexed_data(data):
        if isinstance(data, Mapping):
            return {
                label: data[label] if label in data else data[idx]
                for idx, label in enumerate(item_labels)
            }
        return {
            label: data[idx]
            for idx, label in enumerate(item_labels)
        }

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=item_labels, ordered=True)
    model.capacity = pyo.Param(initialize=capacity, within=pyo.Reals)
    model.item_value = pyo.Param(
        model.item_set,
        initialize=indexed_data(values),
        within=pyo.Reals,
    )
    model.item_weight = pyo.Param(
        model.item_set,
        initialize=indexed_data(weights),
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.item_set, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[label] * model.selected[label]
            for label in model.item_set
        ) <= model.capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_value[label] * model.selected[label]
            for label in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}