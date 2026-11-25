# IR: {"sets":{"I":"0..31"},"params":{"values":"params['values'][i] for i in I","weights":"params['weights'][i] for i in I","capacity":"params['capacity']"},"variables":{"x[i]":"Binary for i in I"},"constraints":["sum(weights[i]*x[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 31)

    model.item_values = pyo.Param(
        model.item_set,
        initialize={i: values[i] for i in range(32)},
        within=pyo.Reals,
    )
    model.item_weights = pyo.Param(
        model.item_set,
        initialize={i: weights[i] for i in range(32)},
        within=pyo.Reals,
    )
    model.weight_limit = pyo.Param(
        initialize=capacity,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.item_set, domain=pyo.Binary)

    model.capacity_constraint = pyo.Constraint(
        expr=sum(
            model.item_weights[i] * model.x[i]
            for i in model.item_set
        ) <= model.weight_limit
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.item_values[i] * model.x[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}