# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5]},"params":{"preferences":"Binary 6x6 matrix read from params['preferences']"},"variables":{"assignment[i,j]":"Binary for each participant i and car j"},"constraints":["assignment[i,j] <= preferences[i][j] for all i,j","sum_j assignment[i,j] <= 1 for each participant i","sum_i assignment[i,j] <= 1 for each car j"],"objective":"maximize sum_i sum_j assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.acceptability = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: preferences[i][j],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, i, j: (
            mdl.assignment[i, j] <= mdl.acceptability[i, j]
        ),
    )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=lambda mdl, i: (
            sum(mdl.assignment[i, j] for j in mdl.cars) <= 1
        ),
    )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=lambda mdl, j: (
            sum(mdl.assignment[i, j] for i in mdl.participants) <= 1
        ),
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