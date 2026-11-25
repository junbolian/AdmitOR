# IR: {"sets":{"crops":["A","B","C"]},"params":["value_A","value_B","value_C","weight_A","weight_B","weight_C","capacity"],"variables":{"selected[crops]":"binary"},"constraints":["sum(weight[crop] * selected[crop] for crop in crops) <= capacity"],"objective":"maximize sum(value[crop] * selected[crop] for crop in crops)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = {
        "A": params["value_A"],
        "B": params["value_B"],
        "C": params["value_C"],
    }
    weights = {
        "A": params["weight_A"],
        "B": params["weight_B"],
        "C": params["weight_C"],
    }
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.crops = pyo.Set(initialize=["A", "B", "C"], ordered=True)
    model.crop_value = pyo.Param(model.crops, initialize=values)
    model.crop_weight = pyo.Param(model.crops, initialize=weights)
    model.truck_capacity = pyo.Param(initialize=capacity)

    model.selected = pyo.Var(model.crops, domain=pyo.Binary)

    model.capacity_constraint = pyo.Constraint(
        expr=sum(
            model.crop_weight[crop] * model.selected[crop]
            for crop in model.crops
        ) <= model.truck_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.crop_value[crop] * model.selected[crop]
            for crop in model.crops
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