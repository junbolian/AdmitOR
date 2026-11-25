# IR: {"sets":{"participants":"0..5","cars":"0..5"},"params":{"preference_matrix":"binary a[i,j], read from params","assignment_cap_per_participant":"participant capacity, read from params","assignment_cap_per_car":"car capacity, read from params"},"variables":{"x[i,j]":"Binary"},"constraints":["sum_j x[i,j] <= assignment_cap_per_participant for each i","sum_i x[i,j] <= assignment_cap_per_car for each j","x[i,j] <= a[i,j] for each i,j"],"objective":"maximize sum_i sum_j x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["assignment_cap_per_participant"]
    car_capacity = params["assignment_cap_per_car"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda model, i, j: preference_matrix[i][j],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity,
        within=pyo.Reals,
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(model, i):
        return (
            sum(model.x[i, j] for j in model.cars)
            <= model.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(model, j):
        return (
            sum(model.x[i, j] for i in model.participants)
            <= model.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def preference_limit_rule(model, i, j):
        return model.x[i, j] <= model.preferences[i, j]

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.x[i, j]
            for i in model.participants
            for j in model.cars
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