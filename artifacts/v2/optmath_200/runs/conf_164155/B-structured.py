# IR: {"sets":{"item_set":"item_0 through item_39"},"params":{"profit":"real[item_set]","resource_coeff":"real[item_set]","capacity":"real[item_set]","resource_budget":"real"},"variables":{"quantity":"nonnegative continuous[item_set]"},"constraints":["quantity[i] <= capacity[i] for each i in item_set","sum(resource_coeff[i] * quantity[i] for i in item_set) <= resource_budget"],"objective":"maximize sum(profit[i] * quantity[i] for i in item_set)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous production-planning problem."""
    item_labels = [f"item_{idx}" for idx in range(40)]

    def item_data(values):
        """Accept sequences or mappings keyed by item labels or indices."""
        if not isinstance(values, Mapping):
            return {
                item: values[idx]
                for idx, item in enumerate(item_labels)
            }

        data = {}
        for idx, item in enumerate(item_labels):
            if item in values:
                data[item] = values[item]
            elif idx in values:
                data[item] = values[idx]
            else:
                data[item] = values[str(idx)]
        return data

    profit_data = item_data(params["profit"])
    resource_data = item_data(params["resource_coeff"])
    capacity_data = item_data(params["capacity"])
    budget = params["resource_budget"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

    model.profit = pyo.Param(
        model.item_set, initialize=profit_data, within=pyo.Reals
    )
    model.resource_coeff = pyo.Param(
        model.item_set, initialize=resource_data, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.item_set, initialize=capacity_data, within=pyo.Reals
    )
    model.resource_budget = pyo.Param(
        initialize=budget, within=pyo.Reals
    )

    model.quantity = pyo.Var(
        model.item_set, domain=pyo.NonNegativeReals
    )

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=lambda mdl, item: mdl.quantity[item] <= mdl.capacity[item],
    )
    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_coeff[item] * model.quantity[item]
            for item in model.item_set
        ) <= model.resource_budget
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}