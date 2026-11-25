# IR: {"sets":{"P":"range(params['participant_count'])","C":"range(params['car_count'])"},"params":{"participant_count":"nonnegative integer; frozen","car_count":"nonnegative integer; frozen","preference":"binary matrix indexed by P x C","participant_capacity":"nonnegative scalar or values indexed by P","car_capacity":"nonnegative scalar or values indexed by C","assignment_value":"real scalar"},"variables":{"x[p,c]":"binary for (p,c) in P x C"},"constraints":["x[p,c] <= preference[p,c] for every (p,c)","sum(x[p,c] for c in C) <= participant_capacity[p] for every p; broadcast scalar capacity","sum(x[p,c] for p in P) <= car_capacity[c] for every c; broadcast scalar capacity"],"objective":"maximize assignment_value * sum(x[p,c] for (p,c) in P x C)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    def capacity_at(capacity, position):
        return capacity if isinstance(capacity, Number) else capacity[position]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(participant_count), ordered=True
    )
    model.cars = pyo.Set(
        initialize=range(car_count), ordered=True
    )

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: preference[participant][car],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize=lambda mdl, participant: capacity_at(
            participant_capacity, participant
        ),
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize=lambda mdl, car: capacity_at(car_capacity, car),
        within=pyo.NonNegativeReals,
    )
    model.assignment_value = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return mdl.x[participant, car] <= mdl.preference[participant, car]

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            None,
            pyo.quicksum(mdl.x[participant, car] for car in mdl.cars),
            mdl.participant_capacity[participant],
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return (
            None,
            pyo.quicksum(
                mdl.x[participant, car]
                for participant in mdl.participants
            ),
            mdl.car_capacity[car],
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_value
        * pyo.quicksum(
            model.x[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignment_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}