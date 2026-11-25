# IR: {"sets":{"P":"0..5","C":"0..5"},"params":{"preferences":"binary[P,C]","participant_capacity":"nonnegative[P]","car_capacity":"nonnegative[C]"},"variables":{"x[P,C]":"binary"},"constraints":["x[p,c] <= preferences[p,c] for all p in P, c in C","sum(x[p,c] for c in C) <= participant_capacity[p] for all p in P","sum(x[p,c] for p in P) <= car_capacity[c] for all c in C"],"objective":"maximize sum(x[p,c] for p in P, c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 5)
    model.C = pyo.RangeSet(0, 5)

    model.preferences = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, p, c: preferences[p][c],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, p: participant_capacity[p],
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.C,
        initialize=lambda mdl, c: car_capacity[c],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.preference_limits = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, p, c: mdl.x[p, c] <= mdl.preferences[p, c],
    )
    model.participant_limits = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: sum(mdl.x[p, c] for c in mdl.C)
        <= mdl.participant_capacity[p],
    )
    model.car_limits = pyo.Constraint(
        model.C,
        rule=lambda mdl, c: sum(mdl.x[p, c] for p in mdl.P)
        <= mdl.car_capacity[c],
    )

    model.total_assignments = pyo.Objective(
        expr=sum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A solution-loading failure may leave the objective unavailable.
        pass

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}