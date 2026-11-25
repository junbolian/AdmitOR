# IR: {"sets":{"participants":[0,1,2,3,4],"cars":[0,1,2,3]},"params":{"preferences":"Optional 5-by-4 binary matrix from params['preferences']; because no preference data are specified, missing preferences default to all ones (all assignments permitted)."},"decision_variables":{"assignment[i,j]":"binary"},"constraints":["assignment[i,j] <= preferences[i][j] for each participant i and car j","sum_j assignment[i,j] <= 1 for each participant i","sum_i assignment[i,j] <= 1 for each car j"],"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    if "preferences" in params:
        preferences = params["preferences"]
    else:
        preferences = [[1 for car in range(4)] for participant in range(5)]

    if len(preferences) != 5 or any(len(row) != 4 for row in preferences):
        return {"objective": None, "status": "invalid_preferences"}
    if any(value not in (0, 1) for row in preferences for value in row):
        return {"objective": None, "status": "invalid_preferences"}

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 3)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): preferences[participant][car]
            for participant in model.participants
            for car in model.cars
        },
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    def participant_rule(instance, participant):
        return sum(
            instance.assignment[participant, car] for car in instance.cars
        ) <= 1

    model.participant_constraints = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_constraints = pyo.Constraint(model.cars, rule=car_rule)

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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}