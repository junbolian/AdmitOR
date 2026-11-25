# IR: {"sets":{"participants":"0..5","cars":"0..5"},"params":{"preference_matrix":"binary a[i,j], read from params","assignment_cap_per_participant":"scalar, read from params","assignment_cap_per_car":"scalar, read from params"},"variables":{"x[i,j]":"binary"},"constraints":["sum_j x[i,j] <= assignment_cap_per_participant for each participant i","sum_i x[i,j] <= assignment_cap_per_car for each car j","x[i,j] <= a[i,j] for each participant i and car j"],"objective":"maximize sum_i sum_j x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_cap = params["assignment_cap_per_participant"]
    car_cap = params["assignment_cap_per_car"]

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.interest = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: preference_matrix[i][j],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_cap,
        within=pyo.Reals,
    )
    model.car_capacity = pyo.Param(
        initialize=car_cap,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(mdl, i):
        return (
            sum(mdl.assignment[i, j] for j in mdl.cars)
            <= mdl.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(mdl, j):
        return (
            sum(mdl.assignment[i, j] for i in mdl.participants)
            <= mdl.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def preference_limit_rule(mdl, i, j):
        return mdl.assignment[i, j] <= mdl.interest[i, j]

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[i, j]
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
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}