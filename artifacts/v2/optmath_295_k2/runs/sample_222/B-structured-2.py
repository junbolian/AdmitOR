# IR: {"sets":{"I":"range(num_packages)"},"params":{"value":"real[I]","weight":"real[I]","capacity":"real","num_packages":"nonnegative integer, frozen"},"variables":{"selected[i]":"binary, i in I"},"constraints":["sum(weight[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(value[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.num_packages = pyo.Param(
        initialize=params["num_packages"],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.package_set = pyo.Set(
        initialize=range(params["num_packages"]),
        ordered=True,
    )
    model.package_value = pyo.Param(
        model.package_set,
        initialize=lambda mdl, i: params["value"][i],
        within=pyo.Reals,
    )
    model.package_weight = pyo.Param(
        model.package_set,
        initialize=lambda mdl, i: params["weight"][i],
        within=pyo.Reals,
    )
    model.vehicle_capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.package_set, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=pyo.quicksum(
            model.package_weight[i] * model.selected[i]
            for i in model.package_set
        ) <= model.vehicle_capacity
    )
    model.total_value = pyo.Objective(
        expr=pyo.quicksum(
            model.package_value[i] * model.selected[i]
            for i in model.package_set
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