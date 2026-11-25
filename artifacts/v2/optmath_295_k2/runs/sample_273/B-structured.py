# IR: {"sets":{"participants":"0..7","cars":"0..7"},"params":{"preference":"binary matrix indexed by participant and car","participant_capacity":"vector indexed by participant","car_capacity":"vector indexed by car","assignment_value":"scalar assignment value"},"variables":{"x[i,j]":"binary"},"constraints":["x[i,j] <= preference[i,j] for all i,j","sum_j x[i,j] <= participant_capacity[i] for all i","sum_i x[i,j] <= car_capacity[j] for all j"],"objective":"maximize assignment_value * sum_i sum_j x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 7)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: preference[i][j],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize=lambda mdl, i: participant_capacity[i],
        within=pyo.Reals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize=lambda mdl, j: car_capacity[j],
        within=pyo.Reals,
    )
    model.assignment_value = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
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
        <= mdl.participant_capacity[i],
    )
    model.car_limits = pyo.Constraint(
        model.cars,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.participants)
        <= mdl.car_capacity[j],
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