# IR: {"sets":{"P":"0..5","C":"0..5"},"params":{"preference_matrix":"Binary[P,C], read from params","unit_assignment_value":"Real, read from params"},"variables":{"assignment[p,c]":"Binary"},"constraints":["For each p: sum(assignment[p,c] for c in C) <= 1","For each c: sum(assignment[p,c] for p in P) <= 1","For each p,c: assignment[p,c] <= preference_matrix[p,c]"],"objective":"maximize unit_assignment_value * sum(assignment[p,c] for p in P for c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.preference_matrix = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, p, c: params["preference_matrix"][p][c],
        within=pyo.Binary,
    )
    model.unit_assignment_value = pyo.Param(
        initialize=params["unit_assignment_value"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_capacity_rule(mdl, p):
        return sum(mdl.assignment[p, c] for c in mdl.cars) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, c):
        return sum(mdl.assignment[p, c] for p in mdl.participants) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    def eligibility_rule(mdl, p, c):
        return mdl.assignment[p, c] <= mdl.preference_matrix[p, c]

    model.eligibility = pyo.Constraint(
        model.participants,
        model.cars,
        rule=eligibility_rule,
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.unit_assignment_value
        * sum(
            model.assignment[p, c]
            for p in model.participants
            for c in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_assignment_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}