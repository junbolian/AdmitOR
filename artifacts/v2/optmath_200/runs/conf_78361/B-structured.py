# IR: {"sets":{"participants":[0,1,2,3,4],"cars":[0,1,2,3,4]},"params":{"assignment_value":"real scalar","participant_capacity":"nonnegative scalar","car_capacity":"nonnegative scalar","preference":"binary matrix indexed by participant and car"},"variables":{"x[i,j]":"binary"},"constraints":["x[i,j] <= preference[i][j] for every participant i and car j","sum_j x[i,j] <= participant_capacity for every participant i","sum_i x[i,j] <= car_capacity for every car j"],"objective":"maximize assignment_value * sum_{i,j} x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 4)

    model.assignment_value = pyo.Param(initialize=assignment_value)
    model.participant_capacity = pyo.Param(initialize=participant_capacity)
    model.car_capacity = pyo.Param(initialize=car_capacity)
    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: preference[i][j],
        within=pyo.Binary,
    )

    model.x = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.preference[i, j],
    )
    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.cars)
        <= mdl.participant_capacity,
    )
    model.car_limits = pyo.Constraint(
        model.cars,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.participants)
        <= mdl.car_capacity,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * sum(model.x[i, j] for i in model.participants for j in model.cars),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}