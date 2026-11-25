# IR: {"sets":{"I":[0,1,2,3,4,5,6,7,8]},"params":{"value[i]":"params['value_'+str(i)] for i in I","weight[i]":"params['weight_'+str(i)] for i in I","capacity":"params['capacity']"},"variables":{"selected[i]":"Binary for i in I"},"constraints":["sum(weight[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(value[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = [
        params["value_0"],
        params["value_1"],
        params["value_2"],
        params["value_3"],
        params["value_4"],
        params["value_5"],
        params["value_6"],
        params["value_7"],
        params["value_8"],
    ]
    weights = [
        params["weight_0"],
        params["weight_1"],
        params["weight_2"],
        params["weight_3"],
        params["weight_4"],
        params["weight_5"],
        params["weight_6"],
        params["weight_7"],
        params["weight_8"],
    ]

    model = pyo.ConcreteModel()
    model.shipments = pyo.RangeSet(0, 8)
    model.shipment_value = pyo.Param(
        model.shipments, initialize=dict(enumerate(values))
    )
    model.shipment_weight = pyo.Param(
        model.shipments, initialize=dict(enumerate(weights))
    )
    model.cargo_capacity = pyo.Param(initialize=params["capacity"])

    model.selected = pyo.Var(model.shipments, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.shipment_weight[i] * model.selected[i]
            for i in model.shipments
        )
        <= model.cargo_capacity
    )
    model.total_value = pyo.Objective(
        expr=sum(
            model.shipment_value[i] * model.selected[i]
            for i in model.shipments
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