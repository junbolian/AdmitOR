# IR: {"sets":{"resources":"0..30"},"params":{"educational_value":"real[resources] from params['educational_value']","cost":"real[resources] from params['cost']","budget":"real from params['budget']"},"decision_variables":{"selected":"binary[resources]"},"constraints":["sum(cost[i] * selected[i] for i in resources) <= budget"],"objective":"maximize sum(educational_value[i] * selected[i] for i in resources)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.resources = pyo.RangeSet(0, 30)

    model.educational_value = pyo.Param(
        model.resources,
        initialize={
            i: params["educational_value"][i] for i in model.resources
        },
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.resources,
        initialize={i: params["cost"][i] for i in model.resources},
        within=pyo.Reals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.resources, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.cost[i] * model.selected[i] for i in model.resources
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_educational_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}