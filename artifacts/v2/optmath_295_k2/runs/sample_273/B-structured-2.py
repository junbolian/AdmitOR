# IR: {"sets":{"P":"0..7","C":"0..7"},"params":{"preference":"binary[P,C] from params['preference']","participant_capacity":"real[P] from params['participant_capacity']; scalar input broadcasts","car_capacity":"real[C] from params['car_capacity']; scalar input broadcasts","assignment_value":"real scalar from params['assignment_value']"},"variables":{"x[P,C]":"binary"},"constraints":["x[p,c] <= preference[p,c] for p in P, c in C","sum(x[p,c] for c in C) <= participant_capacity[p] for p in P","sum(x[p,c] for p in P) <= car_capacity[c] for c in C"],"objective":"maximize assignment_value * sum(x[p,c] for p in P, c in C)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    def capacity_at(values, idx):
        if isinstance(values, Number):
            return values
        return values[idx]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 7)
    model.C = pyo.RangeSet(0, 7)

    model.preference = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, p, c: preference[p][c],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, p: capacity_at(participant_capacity, p),
        within=pyo.Reals,
    )
    model.car_capacity = pyo.Param(
        model.C,
        initialize=lambda mdl, c: capacity_at(car_capacity, c),
        within=pyo.Reals,
    )
    model.assignment_value = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.preference_limit = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, p, c: mdl.x[p, c] <= mdl.preference[p, c],
    )
    model.participant_limit = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: (
            sum(mdl.x[p, c] for c in mdl.C)
            <= mdl.participant_capacity[p]
        ),
    )
    model.car_limit = pyo.Constraint(
        model.C,
        rule=lambda mdl, c: (
            sum(mdl.x[p, c] for p in mdl.P)
            <= mdl.car_capacity[c]
        ),
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * sum(model.x[p, c] for p in model.P for c in model.C),
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