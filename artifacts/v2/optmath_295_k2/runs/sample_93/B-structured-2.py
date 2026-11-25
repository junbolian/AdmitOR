# IR: {"sets":{"participants":"0..7","cars":"0..6"},"params":{"preferences":{"source":"params['preferences']","shape":[8,7],"domain":"binary"}},"variables":{"assignment[i,j]":{"domain":"binary","indices":["participants","cars"]}},"constraints":["assignment[i,j] <= preferences[i,j] for each participant i and car j","sum_j assignment[i,j] <= 1 for each participant i","sum_i assignment[i,j] <= 1 for each car j"],"objective":{"sense":"maximize","expression":"sum_i sum_j assignment[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 6)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda instance, i, j: preferences[i][j],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda instance, i, j: (
            instance.assignment[i, j] <= instance.preferences[i, j]
        ),
    )

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=lambda instance, i: (
            sum(instance.assignment[i, j] for j in instance.cars) <= 1
        ),
    )

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=lambda instance, j: (
            sum(instance.assignment[i, j] for i in instance.participants) <= 1
        ),
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[i, j]
            for i in model.participants
            for j in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}