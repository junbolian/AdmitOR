# IR: {"sets":{"P":"{0,...,6}","C":"{0,...,6}"},"params":{"preferences":"params['preferences']; adjacency list keyed by integer or string participant indices; missing participants have no acceptable cars; missing preferences returns missing_preferences"},"variables":{"x[p,c]":"binary for p in P, c in C"},"constraints":["x[p,c] <= indicator(c in preferences[p]) for every p in P, c in C","sum(c in C) x[p,c] <= 1 for every p in P","sum(p in P) x[p,c] <= 1 for every c in C"],"objective":"maximize sum(p in P,c in C) x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    if "preferences" not in params:
        return {"objective": None, "status": "missing_preferences"}

    preferences = params["preferences"]
    allowed_cars = {
        participant: set(
            preferences.get(
                participant,
                preferences.get(str(participant), []),
            )
        )
        for participant in range(7)
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(instance, participant, car):
        allowed = int(car in allowed_cars[participant])
        return instance.assignment[participant, car] <= allowed

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
        ) <= 1

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_rule,
    )

    def car_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}