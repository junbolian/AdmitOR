# IR: {"sets":{"P":"range(params['n_participants'])","C":"range(params['n_cars'])"},"params":{"n_participants":"nonnegative integer","n_cars":"nonnegative integer","preference":"binary matrix[P][C]","participant_capacity":"nonnegative vector[P], or scalar broadcast to P","car_capacity":"nonnegative vector[C], or scalar broadcast to C","objective_coeff":"real scalar"},"variables":{"x[P,C]":"binary"},"constraints":["sum(x[p,c] for c in C) <= participant_capacity[p] for each p in P","sum(x[p,c] for p in P) <= car_capacity[c] for each c in C","x[p,c] <= preference[p,c] for each (p,c) in P x C"],"objective":"maximize objective_coeff * sum(x[p,c] for (p,c) in P x C)"}

from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(params["n_participants"]),
        ordered=True,
    )
    model.cars = pyo.Set(
        initialize=range(params["n_cars"]),
        ordered=True,
    )

    participant_capacities = params["participant_capacity"]
    car_capacities = params["car_capacity"]

    def capacity_at(capacities, position):
        if isinstance(capacities, Real):
            return capacities
        return capacities[position]

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: (
            params["preference"][participant][car]
        ),
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize=lambda mdl, participant: capacity_at(
            participant_capacities, participant
        ),
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize=lambda mdl, car: capacity_at(car_capacities, car),
        within=pyo.NonNegativeReals,
    )
    model.objective_coeff = pyo.Param(
        initialize=params["objective_coeff"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            None,
            pyo.quicksum(mdl.x[participant, car] for car in mdl.cars),
            mdl.participant_capacity[participant],
        )

    model.participant_limits = pyo.Constraint(
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

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, participant, car: (
            mdl.x[participant, car] <= mdl.preference[participant, car]
        ),
    )

    model.total_reward = pyo.Objective(
        expr=model.objective_coeff
        * pyo.quicksum(
            model.x[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_reward))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}