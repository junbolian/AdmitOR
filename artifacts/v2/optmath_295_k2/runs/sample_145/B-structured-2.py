# IR: {"sets":{"resources":"0..30"},"params":{"educational_value":"nonnegative real[resources] from params","cost":"nonnegative real[resources] from params","budget":"nonnegative real from params"},"variables":{"selected":"binary[resources]"},"constraints":["sum(cost[i]*selected[i] for i in resources) <= budget"],"objective":"maximize sum(educational_value[i]*selected[i] for i in resources)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.resources = pyo.RangeSet(0, 30)

    model.educational_value = pyo.Param(
        model.resources,
        initialize={
            resource: params["educational_value"][resource]
            for resource in model.resources
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.resources,
        initialize={
            resource: params["cost"][resource]
            for resource in model.resources
        },
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.resources, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.cost[resource] * model.selected[resource]
            for resource in model.resources
        ) <= model.budget
    )

    model.total_educational_value = pyo.Objective(
        expr=sum(
            model.educational_value[resource] * model.selected[resource]
            for resource in model.resources
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_educational_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}