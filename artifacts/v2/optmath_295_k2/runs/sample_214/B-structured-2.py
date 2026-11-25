# IR: {"sets":{"P":"range(params['n_participants'])","C":"range(params['n_cars'])"},"params":{"preference[p,c]":"params['preference'][p][c], binary","participant_capacity[p]":"params['participant_capacity'][p], nonnegative","car_capacity[c]":"params['car_capacity'][c], nonnegative","n_participants":"params['n_participants'], participant count","n_cars":"params['n_cars'], car count","objective_coeff":"params['objective_coeff'], real"},"variables":{"x[p,c]":"Binary"},"constraints":["sum(x[p,c] for c in C) <= participant_capacity[p] for each p in P","sum(x[p,c] for p in P) <= car_capacity[c] for each c in C","x[p,c] <= preference[p,c] for each (p,c) in P x C"],"objective":"maximize objective_coeff * sum(x[p,c] for (p,c) in P x C)"}

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
        initialize=lambda mdl, participant: (
            params["participant_capacity"][participant]
        ),
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize=lambda mdl, car: params["car_capacity"][car],
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

    def participant_limit_rule(mdl, participant):
        return (
            pyo.quicksum(mdl.x[participant, car] for car in mdl.cars)
            <= mdl.participant_capacity[participant]
        )

    model.participant_limit = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(mdl, car):
        return (
            pyo.quicksum(
                mdl.x[participant, car]
                for participant in mdl.participants
            )
            <= mdl.car_capacity[car]
        )

    model.car_limit = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    model.preference_limit = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_reward))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}