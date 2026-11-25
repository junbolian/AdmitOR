# IR: {"sets":{"resources":"0..30"},"params":{"educational_value":"nonnegative real[resources], from params","cost":"nonnegative real[resources], from params","budget":"nonnegative real, from params"},"variables":{"selected":"binary[resources]"},"constraints":["sum(cost[i]*selected[i] for i in resources) <= budget"],"objective":"maximize sum(educational_value[i]*selected[i] for i in resources)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    educational_value = params["educational_value"]
    cost = params["cost"]
    budget = params["budget"]

    model = pyo.ConcreteModel()
    model.resources = pyo.RangeSet(0, 30)

    model.educational_value = pyo.Param(
        model.resources,
        initialize=lambda _, i: educational_value[i],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.resources,
        initialize=lambda _, i: cost[i],
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(
        initialize=budget,
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.resources, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.cost[i] * model.selected[i]
            for i in model.resources
        ) <= model.budget
    )

    model.total_educational_value = pyo.Objective(
        expr=sum(
            model.educational_value[i] * model.selected[i]
            for i in model.resources
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_educational_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}