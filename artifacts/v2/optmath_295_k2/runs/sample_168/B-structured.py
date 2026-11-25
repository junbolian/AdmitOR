# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])"},"params":{"num_participants":"frozen participant count","num_cars":"frozen car count","participant_0_4_interest":"binary interest for participants 0-3 in every car","participant_4_car_1_interest":"binary interest for participant 4 in car 1","participant_4_forbidden_interest":"binary interest for participant 4 in cars other than 1"},"variables":{"x[P,C]":"Binary"},"constraints":["For each i in P: sum(x[i,j] for j in C) <= 1","For each j in C: sum(x[i,j] for i in P) <= 1","For each (i,j): x[i,j] <= participant_0_4_interest if i < 4, otherwise participant_4_car_1_interest if j == 1, otherwise participant_4_forbidden_interest"],"objective":"maximize sum(x[i,j] for i in P for j in C)"}

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

    model.x = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def participant_limit_rule(instance, participant):
        return sum(
            instance.x[participant, car] for car in instance.cars
        ) <= 1

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return sum(
            instance.x[participant, car]
            for participant in instance.participants
        ) <= 1

    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

    def preference_limit_rule(instance, participant, car):
        if participant < 4:
            interest = general_interest
        elif car == 1:
            interest = car_1_interest
        else:
            interest = forbidden_interest
        return instance.x[participant, car] <= interest

    model.preference_limit = pyo.Constraint(
        model.participants, model.cars, rule=preference_limit_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.x[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}