# IR: {"sets":{"I":[0,1,2,3,4,5,6,7,8]},"params":{"value":["value_0","value_1","value_2","value_3","value_4","value_5","value_6","value_7","value_8"],"weight":["weight_0","weight_1","weight_2","weight_3","weight_4","weight_5","weight_6","weight_7","weight_8"],"capacity":"capacity"},"variables":{"selected[i]":{"indices":"I","type":"binary"}},"constraints":["sum(weight[i]*selected[i] for i in I) <= capacity"],"objective":{"sense":"maximize","expression":"sum(value[i]*selected[i] for i in I)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.shipments = pyo.RangeSet(0, 8)

    values = {
        0: params["value_0"],
        1: params["value_1"],
        2: params["value_2"],
        3: params["value_3"],
        4: params["value_4"],
        5: params["value_5"],
        6: params["value_6"],
        7: params["value_7"],
        8: params["value_8"],
    }
    weights = {
        0: params["weight_0"],
        1: params["weight_1"],
        2: params["weight_2"],
        3: params["weight_3"],
        4: params["weight_4"],
        5: params["weight_5"],
        6: params["weight_6"],
        7: params["weight_7"],
        8: params["weight_8"],
    }

    model.shipment_value = pyo.Param(
        model.shipments, initialize=values, within=pyo.Reals
    )
    model.shipment_weight = pyo.Param(
        model.shipments, initialize=weights, within=pyo.Reals
    )
    model.weight_capacity = pyo.Param(
        initialize=params["capacity"], within=pyo.Reals
    )

    model.selected = pyo.Var(model.shipments, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.shipment_weight[i] * model.selected[i]
            for i in model.shipments
        ) <= model.weight_capacity
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}