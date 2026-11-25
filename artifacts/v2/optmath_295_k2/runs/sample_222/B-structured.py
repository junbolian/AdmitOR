# IR: {"sets":{"I":"range(params['num_packages'])"},"params":{"num_packages":"nonnegative integer, frozen index-set size","value":"value[i] for i in I","weight":"weight[i] for i in I","capacity":"maximum total weight"},"variables":{"selected[i]":"binary for i in I"},"constraints":["sum(weight[i]*selected[i] for i in I) <= capacity"],"objective":"maximize sum(value[i]*selected[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.num_packages = pyo.Param(
        initialize=params["num_packages"],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.package_ids = pyo.Set(
        initialize=range(int(pyo.value(model.num_packages))),
        ordered=True,
    )

    model.package_value = pyo.Param(
        model.package_ids,
        initialize=lambda mdl, idx: params["value"][idx],
        within=pyo.Reals,
    )
    model.package_weight = pyo.Param(
        model.package_ids,
        initialize=lambda mdl, idx: params["weight"][idx],
        within=pyo.Reals,
    )
    model.vehicle_capacity = pyo.Param(
        initialize=params["capacity"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.package_ids, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=pyo.quicksum(
            model.package_weight[idx] * model.selected[idx]
            for idx in model.package_ids
        ) <= model.vehicle_capacity
    )

    model.total_value = pyo.Objective(
        expr=pyo.quicksum(
            model.package_value[idx] * model.selected[idx]
            for idx in model.package_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Still use objective retrieval below as the success criterion.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}