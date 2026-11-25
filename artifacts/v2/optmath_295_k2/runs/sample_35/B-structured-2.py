# IR: {"sets":{"I":["item_0","item_1","item_2","item_3","item_4","item_5","item_6","item_7","item_8","item_9","item_10"]},"params":{"profit":"real[I]","resource_consumption":"real[I]","resource_capacity":"real","production_capacity":"real[I]"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in I) <= resource_capacity","quantity[i] <= production_capacity[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve with indexed inputs supplied as sequences or label/integer mappings."""
    item_labels = tuple(f"item_{idx}" for idx in range(11))

    profit_data = params["profit"]
    resource_data = params["resource_consumption"]
    resource_capacity_data = params["resource_capacity"]
    production_capacity_data = params["production_capacity"]

    def indexed_values(data):
        if isinstance(data, Mapping):
            return {
                item: data[item] if item in data else data[idx]
                for idx, item in enumerate(item_labels)
            }
        return {
            item: data[idx]
            for idx, item in enumerate(item_labels)
        }

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

    model.profit = pyo.Param(
        model.item_set,
        initialize=indexed_values(profit_data),
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize=indexed_values(resource_data),
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity_data,
        within=pyo.Reals,
    )
    model.production_capacity = pyo.Param(
        model.item_set,
        initialize=indexed_values(production_capacity_data),
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[item] * model.quantity[item]
            for item in model.item_set
        )
        <= model.resource_capacity
    )

    def capacity_rule(block, item):
        return block.quantity[item] <= block.production_capacity[item]

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[item] * model.quantity[item]
            for item in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # Objective retrieval below is the sole test for success.

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}