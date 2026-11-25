# IR: {"sets":{"participants":[0,1,2,3,4],"cars":[0,1,2,3]},"params":{"preferences":"optional 5x4 binary matrix from params['preferences']; because no preference data are supplied, omitted preferences default to 1 (no preference restrictions)"},"variables":{"assignment[i,j]":"binary"},"constraints":{"preference":"assignment[i,j] <= preferences[i][j] for each participant i and car j","participant_capacity":"sum_j assignment[i,j] <= 1 for each participant i","car_capacity":"sum_i assignment[i,j] <= 1 for each car j"},"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize assignments; absent preference data impose no restrictions."""
    participants = range(5)
    cars = range(4)

    if "preferences" in params:
        preferences = params["preferences"]
    else:
        preferences = [[1 for car in cars] for participant in participants]

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(initialize=participants, ordered=True)
    model.cars = pyo.Set(initialize=cars, ordered=True)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        within=pyo.Binary,
        initialize={
            (participant, car): preferences[participant][car]
            for participant in participants
            for car in cars
        },
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    def participant_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
        ) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars, rule=car_rule
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}