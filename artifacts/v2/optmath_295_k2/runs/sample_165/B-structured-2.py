# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":{"preference_matrix":"binary[P,C]","assignment_capacity_per_participant":"scalar","assignment_capacity_per_car":"scalar","num_participants":"frozen nonnegative integer","num_cars":"frozen nonnegative integer","objective_weight_per_assignment":"scalar"},"variables":{"x[P,C]":"binary"},"constraints":["sum(x[i,j] for j in C) <= assignment_capacity_per_participant for i in P","sum(x[i,j] for i in P) <= assignment_capacity_per_car for j in C","x[i,j] <= preference_matrix[i,j] for (i,j) in P x C"],"objective":"maximize objective_weight_per_assignment * sum(x[i,j] for (i,j) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["assignment_capacity_per_participant"]
    car_capacity = params["assignment_capacity_per_car"]
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    assignment_weight = params["objective_weight_per_assignment"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (i, j): preference_matrix[i][j]
            for i in model.participants
            for j in model.cars
        },
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity, within=pyo.Reals
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity, within=pyo.Reals
    )
    model.assignment_weight = pyo.Param(
        initialize=assignment_weight, within=pyo.Reals
    )

    model.x = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def participant_limit_rule(instance, i):
        return (
            None,
            pyo.quicksum(instance.x[i, j] for j in instance.cars),
            instance.participant_capacity,
        )

    def car_limit_rule(instance, j):
        return (
            None,
            pyo.quicksum(instance.x[i, j] for i in instance.participants),
            instance.car_capacity,
        )

    def preference_limit_rule(instance, i, j):
        return instance.x[i, j] <= instance.preferences[i, j]

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )
    model.car_limits = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )
    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_limit_rule
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_weight
        * pyo.quicksum(
            model.x[i, j]
            for i in model.participants
            for j in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignment_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}