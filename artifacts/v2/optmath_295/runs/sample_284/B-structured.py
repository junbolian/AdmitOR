# IR: {"sets":{"participants":[0,1,2,3,4],"cars":[0,1,2,3]},"params":{"preferences":{"source":"params['preferences']","type":"binary","shape":[5,4],"if_missing":"return objective=None, status=missing_preferences; preferences cannot be inferred"}},"decision_variables":{"assignment[i,j]":{"type":"binary","indices":["participants","cars"]}},"constraints":["assignment[i,j] <= preferences[i,j] for every participant i and car j","sum_j assignment[i,j] <= 1 for every participant i","sum_i assignment[i,j] <= 1 for every car j"],"objective":{"sense":"maximize","expression":"sum_i sum_j assignment[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the assignment problem when a 5-by-4 preference matrix is supplied."""
    # No preference data were specified in the problem's PARAMS section.
    # Report missing input rather than inventing participants' preferences.
    if "preferences" not in params:
        return {"objective": None, "status": "missing_preferences"}

    preferences = params["preferences"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 3)

    model.preference_data = pyo.Param(
        model.participants,
        model.cars,
        within=pyo.Binary,
        initialize=lambda mdl, participant, car: preferences[participant][car],
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, participant, car: (
            mdl.assignment[participant, car]
            <= mdl.preference_data[participant, car]
        ),
    )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=lambda mdl, participant: (
            sum(mdl.assignment[participant, car] for car in mdl.cars) <= 1
        ),
    )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=lambda mdl, car: (
            sum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            )
            <= 1
        ),
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}