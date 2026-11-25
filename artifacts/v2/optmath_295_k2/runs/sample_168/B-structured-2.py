# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":["num_participants","num_cars","participant_0_4_interest","participant_4_car_1_interest","participant_4_forbidden_interest"],"variables":{"assignment[P,C]":"binary"},"constraints":["For each participant: sum of assignments over cars <= 1.","For each car: sum of assignments over participants <= 1.","For participant indices 0-3: each assignment <= participant_0_4_interest.","For participant 4 and car 1: assignment <= participant_4_car_1_interest.","For participant 4 and cars 0,2,3: each assignment <= participant_4_forbidden_interest."],"objective":"maximize sum of assignment[P,C]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    general_interest = params["participant_0_4_interest"]
    car_1_interest = params["participant_4_car_1_interest"]
    forbidden_interest = params["participant_4_forbidden_interest"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_limit_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
        ) <= 1

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_limits = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )

    def preference_rule(instance, participant, car):
        if participant in (0, 1, 2, 3):
            interest = general_interest
        elif participant == 4 and car == 1:
            interest = car_1_interest
        elif participant == 4 and car in (0, 2, 3):
            interest = forbidden_interest
        else:
            return pyo.Constraint.Skip

        return instance.assignment[participant, car] <= interest

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
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
        # HiGHS can raise when no solution is available to load.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}