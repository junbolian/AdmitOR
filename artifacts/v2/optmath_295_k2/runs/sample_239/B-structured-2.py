# IR: {"sets":{"item_ids":[0,1,2]},"params":{"item_value[i]":"params['value_item'+str(i)]","item_weight[i]":"params['weight_item'+str(i)]","vehicle_capacity":"params['capacity']"},"decision_variables":{"selected[i]":"binary for i in item_ids"},"constraints":["sum(item_weight[i]*selected[i] for i in item_ids) <= vehicle_capacity"],"objective":"maximize sum(item_value[i]*selected[i] for i in item_ids)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.item_ids = pyo.Set(initialize=[0, 1, 2], ordered=True)

    model.item_value = pyo.Param(
        model.item_ids,
        initialize={
            0: params["value_item0"],
            1: params["value_item1"],
            2: params["value_item2"],
        },
    )

    model.item_weight = pyo.Param(
        model.item_ids,
        initialize={
            0: params["weight_item0"],
            1: params["weight_item1"],
            2: params["weight_item2"],
        },
    )

    model.vehicle_capacity = pyo.Param(initialize=params["capacity"])

    model.selected = pyo.Var(model.item_ids, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.item_weight[item_id] * model.selected[item_id]
            for item_id in model.item_ids
        )
        <= model.vehicle_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_value[item_id] * model.selected[item_id]
            for item_id in model.item_ids
        ),
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