# IR: {"sets":{"participants":"range(num_participants)","cars":"range(num_cars)"},"params":{"num_participants":"params['num_participants']","num_cars":"params['num_cars']","preference_0":"params['preference_0']","preference_1":"params['preference_1']","preference_2":"params['preference_2']","preference_3":"params['preference_3']","preference_4":"params['preference_4']","preference_5":"params['preference_5']"},"variables":{"assignment[i,j]":"Binary for each participant i and car j"},"constraints":["assignment[i,j] <= preference_i[j] for every i,j","sum_j assignment[i,j] <= 1 for every i","sum_i assignment[i,j] <= 1 for every j"],"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = (
        params["preference_0"],
        params["preference_1"],
        params["preference_2"],
        params["preference_3"],
        params["preference_4"],
        params["preference_5"],
    )

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.acceptability = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): preferences[participant][car]
            for participant in range(num_participants)
            for car in range(num_cars)
        },
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.acceptability[participant, car]
        )

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    def participant_rule(instance, participant):
        return (
            pyo.quicksum(
                instance.assignment[participant, car]
                for car in instance.cars
            )
            <= 1
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(instance, car):
        return (
            pyo.quicksum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= 1
        )

    model.car_limits = pyo.Constraint(model.cars, rule=car_rule)

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
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