# IR: {"sets":{"P":"{0,...,6}","C":"{0,...,6}"},"params":{"preferences":"params['preferences']; required adjacency mapping with integer or string participant keys","allowed[p,c]":"1 if c is in preferences[p], otherwise 0; absent participant entries mean no acceptable cars"},"variables":{"assignment[p,c]":"Binary for all p in P, c in C"},"constraints":["assignment[p,c] <= allowed[p,c] for all p in P, c in C","sum(c in C) assignment[p,c] <= 1 for all p in P","sum(p in P) assignment[p,c] <= 1 for all c in C"],"objective":"maximize sum(p in P,c in C) assignment[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Missing preferences cannot be inferred without inventing input data.
    if "preferences" not in params:
        return {"objective": None, "status": "missing_preferences"}

    preferences = params["preferences"]
    if not isinstance(preferences, dict):
        return {"objective": None, "status": "invalid_preferences"}

    acceptable_cars = {}
    for participant in range(7):
        choices = preferences.get(
            participant, preferences.get(str(participant), [])
        )
        if not isinstance(choices, (list, tuple, set, frozenset)):
            return {"objective": None, "status": "invalid_preferences"}
        if any(car not in range(7) for car in choices):
            return {"objective": None, "status": "invalid_car_index"}
        acceptable_cars[participant] = set(choices)

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)

    model.allowed = pyo.Param(
        model.participants,
        model.cars,
        within=pyo.Binary,
        initialize=lambda mdl, participant, car: int(
            car in acceptable_cars[participant]
        ),
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return mdl.assignment[participant, car] <= mdl.allowed[participant, car]

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_rule(mdl, participant):
        return sum(
            mdl.assignment[participant, car] for car in mdl.cars
        ) <= 1

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_rule,
    )

    def car_rule(mdl, car):
        return sum(
            mdl.assignment[participant, car]
            for participant in mdl.participants
        ) <= 1

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_rule,
    )

    model.total_matches = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
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
        obj_val = float(pyo.value(model.total_matches))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}