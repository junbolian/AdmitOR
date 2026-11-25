# IR: {"sets":{"participants":"0..5","cars":"0..6"},"params":{"preference_matrix":"binary[participants,cars]","participant_capacity":"scalar","car_capacity":"scalar","assignment_value":"scalar"},"variables":{"x[participants,cars]":"binary"},"constraints":["x[i,j] <= preference_matrix[i,j] for all i,j","sum_j x[i,j] <= participant_capacity for all i","sum_i x[i,j] <= car_capacity for all j"],"objective":"maximize assignment_value * sum_i sum_j x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 6)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (i, j): preferences[i][j]
            for i in model.participants
            for j in model.cars
        },
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(initialize=participant_capacity)
    model.car_capacity = pyo.Param(initialize=car_capacity)
    model.assignment_value = pyo.Param(initialize=assignment_value)

    model.x = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def eligibility_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.preferences[i, j]

    model.eligibility_constraints = pyo.Constraint(
        model.participants, model.cars, rule=eligibility_rule
    )

    def participant_limit_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.cars)
            <= mdl.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(mdl, j):
        return (
            sum(mdl.x[i, j] for i in mdl.participants)
            <= mdl.car_capacity
        )

    model.car_limits = pyo.Constraint(model.cars, rule=car_limit_rule)

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * sum(
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
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}