# IR: {"sets":{"P":"range(params['participants'])","C":"range(params['cars'])"},"params":{"participants":"nonnegative integer","cars":"nonnegative integer","participant_capacity":"nonnegative integer","car_capacity":"nonnegative integer","preference":"binary matrix indexed by P,C"},"variables":{"x[p,c]":"Binary for p in P, c in C"},"constraints":["x[p,c] <= preference[p,c] for p in P, c in C","sum(x[p,c] for c in C) <= participant_capacity for p in P","sum(x[p,c] for p in P) <= car_capacity for c in C"],"objective":"maximize sum(x[p,c] for p in P, c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participant_set = pyo.Set(
        initialize=range(params["participants"]), ordered=True
    )
    model.car_set = pyo.Set(
        initialize=range(params["cars"]), ordered=True
    )

    model.participant_limit = pyo.Param(
        initialize=params["participant_capacity"],
        within=pyo.NonNegativeIntegers,
    )
    model.car_limit = pyo.Param(
        initialize=params["car_capacity"],
        within=pyo.NonNegativeIntegers,
    )
    model.interest = pyo.Param(
        model.participant_set,
        model.car_set,
        initialize=lambda mdl, participant, car: params["preference"][participant][car],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participant_set,
        model.car_set,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return mdl.assignment[participant, car] <= mdl.interest[participant, car]

    model.preference_constraints = pyo.Constraint(
        model.participant_set,
        model.car_set,
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car] for car in mdl.car_set
            ),
            mdl.participant_limit,
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.participant_set,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participant_set
            ),
            mdl.car_limit,
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.car_set,
        rule=car_capacity_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[participant, car]
            for participant in model.participant_set
            for car in model.car_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}