# IR: {"sets":{"participants":[0,1,2,3],"cars":[0,1,2,3,4],"preferred_pairs":[[0,2],[0,4],[2,0],[2,4],[3,0],[3,4]]},"params":{},"decision_variables":{"assignment[p,c]":"binary for every participant p and car c"},"constraints":["For each participant p: sum_c assignment[p,c] <= 1.","For each car c: sum_p assignment[p,c] <= 1.","For every pair (p,c): assignment[p,c] <= indicator((p,c) in preferred_pairs)."],"objective":"maximize sum_p sum_c assignment[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=range(4), ordered=True)
    model.cars = pyo.Set(initialize=range(5), ordered=True)

    preferred_pairs = {
        (0, 2),
        (0, 4),
        (2, 0),
        (2, 4),
        (3, 0),
        (3, 4),
    }

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_limit = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def preference_limit_rule(instance, participant, car):
        return instance.assignment[participant, car] <= int(
            (participant, car) in preferred_pairs
        )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}