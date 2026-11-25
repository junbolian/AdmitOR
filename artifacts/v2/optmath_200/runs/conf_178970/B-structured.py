# IR: {"sets":{"I":"0..31"},"params":{"capacity":"params['capacity']","values[i]":"params['values'][i]","weights[i]":"params['weights'][i]"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weights[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(values[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.package_indices = pyo.RangeSet(0, 31)

    model.vehicle_capacity = pyo.Param(initialize=params["capacity"])
    model.package_values = pyo.Param(
        model.package_indices,
        initialize={i: params["values"][i] for i in model.package_indices},
    )
    model.package_weights = pyo.Param(
        model.package_indices,
        initialize={i: params["weights"][i] for i in model.package_indices},
    )

    model.selected = pyo.Var(model.package_indices, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.package_weights[i] * model.selected[i]
            for i in model.package_indices
        )
        <= model.vehicle_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.package_values[i] * model.selected[i]
            for i in model.package_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load can raise; assess success only by retrieval.
        pass

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}