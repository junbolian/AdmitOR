# IR: {"sets":{"participants":[0,1,2,3,4,5,6],"cars":[0,1,2,3,4,5,6],"interested_pairs":[[0,0],[0,6],[1,0],[1,1],[1,2],[1,4],[1,5],[2,0],[3,1],[3,2],[3,5],[4,0],[5,1],[5,4]]},"params":{"preference_value":"binary scalar from params['preference_value']","preference[i,j]":"preference_value if (i,j) is in interested_pairs; otherwise 0"},"variables":{"assignment[i,j]":"Binary"},"constraints":["assignment[i,j] <= preference[i,j] for every participant i and car j","sum_j assignment[i,j] <= 1 for every participant i","sum_i assignment[i,j] <= 1 for every car j"],"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_value = params["preference_value"]
    if preference_value not in (0, 1):
        return {"objective": None, "status": "invalid_preference_value"}

    interested_pairs = {
        (0, 0), (0, 6),
        (1, 0), (1, 1), (1, 2), (1, 4), (1, 5),
        (2, 0),
        (3, 1), (3, 2), (3, 5),
        (4, 0),
        (5, 1), (5, 4),
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)
    model.interested_pairs = pyo.Set(
        dimen=2,
        within=model.participants * model.cars,
        initialize=interested_pairs,
    )
    model.preference_value = pyo.Param(
        initialize=preference_value,
        within=pyo.Binary,
    )

    def preference_initializer(model, participant, car):
        if (participant, car) in model.interested_pairs:
            return pyo.value(model.preference_value)
        return 0

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=preference_initializer,
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(model, participant, car):
        return (
            model.assignment[participant, car]
            <= model.preference[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_rule(model, participant):
        return sum(
            model.assignment[participant, car] for car in model.cars
        ) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_rule,
    )

    def car_rule(model, car):
        return sum(
            model.assignment[participant, car]
            for participant in model.participants
        ) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}