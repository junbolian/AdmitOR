# IR: {"sets":{"P":"0..6","C":"0..6"},"params":{"participant_capacity":"nonnegative[P] from params; scalar inputs broadcast","car_capacity":"nonnegative[C] from params; scalar inputs broadcast","preference":"binary[P,C] from params","assignment_value":"real scalar from params"},"variables":{"x[P,C]":"binary"},"constraints":["x[p,c] <= preference[p,c] for all p,c","sum(x[p,c] for c in C) <= participant_capacity[p] for all p","sum(x[p,c] for p in P) <= car_capacity[c] for all c"],"objective":"maximize assignment_value * sum(x[p,c] for p in P for c in C)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_capacities = params["participant_capacity"]
    car_capacities = params["car_capacity"]
    preferences = params["preference"]
    assignment_value = params["assignment_value"]

    def indexed_capacity(values, position):
        return values if isinstance(values, Number) else values[position]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 6)
    model.C = pyo.RangeSet(0, 6)

    model.participant_capacity = pyo.Param(
        model.P,
        initialize={
            participant: indexed_capacity(participant_capacities, participant)
            for participant in model.P
        },
        within=pyo.NonNegativeReals,
    )

    model.car_capacity = pyo.Param(
        model.C,
        initialize={
            car: indexed_capacity(car_capacities, car)
            for car in model.C
        },
        within=pyo.NonNegativeReals,
    )

    model.preference = pyo.Param(
        model.P,
        model.C,
        initialize={
            (participant, car): preferences[participant][car]
            for participant in model.P
            for car in model.C
        },
        within=pyo.Binary,
    )

    model.assignment_value = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def eligibility_rule(instance, participant, car):
        return (
            instance.x[participant, car]
            <= instance.preference[participant, car]
        )

    model.eligibility_constraints = pyo.Constraint(
        model.P,
        model.C,
        rule=eligibility_rule,
    )

    def participant_capacity_rule(instance, participant):
        return (
            sum(instance.x[participant, car] for car in instance.C)
            <= instance.participant_capacity[participant]
        )

    model.participant_constraints = pyo.Constraint(
        model.P,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(instance, car):
        return (
            sum(instance.x[participant, car] for participant in instance.P)
            <= instance.car_capacity[car]
        )

    model.car_constraints = pyo.Constraint(
        model.C,
        rule=car_capacity_rule,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * sum(
            model.x[participant, car]
            for participant in model.P
            for car in model.C
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unsuccessful solve can raise before loading a solution.
        # Success is determined exclusively by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}