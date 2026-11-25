# IR: {"sets":{"packages":"0..10"},"params":{"package_values[i]":"params['values'][i]","package_weights[i]":"params['weights'][i]","vehicle_capacity":"params['capacity']"},"variables":{"selected[i]":"Binary"},"constraints":["sum(package_weights[i]*selected[i] for i in packages) <= vehicle_capacity"],"objective":"maximize sum(package_values[i]*selected[i] for i in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 10)

    model.package_values = pyo.Param(
        model.packages,
        initialize={i: params["values"][i] for i in model.packages},
        within=pyo.Reals,
    )
    model.package_weights = pyo.Param(
        model.packages,
        initialize={i: params["weights"][i] for i in model.packages},
        within=pyo.Reals,
    )
    model.vehicle_capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.packages, domain=pyo.Binary)

    model.weight_limit = pyo.Constraint(
        expr=sum(
            model.package_weights[i] * model.selected[i]
            for i in model.packages
        ) <= model.vehicle_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.package_values[i] * model.selected[i]
            for i in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}