# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5]},"params":{"preference":{"source":"params['preference']","index":["participants","cars"],"domain":"Binary"},"assignment_value":{"source":"params['assignment_value']","domain":"Reals"}},"variables":{"assigned":{"index":["participants","cars"],"domain":"Binary"}},"constraints":["sum(assigned[i,j] for j in cars) <= 1 for each i in participants","sum(assigned[i,j] for i in participants) <= 1 for each j in cars","assigned[i,j] <= preference[i,j] for each (i,j)"],"objective":"maximize assignment_value * sum(assigned[i,j] for i in participants for j in cars)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, i, j: params["preference"][i][j],
        within=pyo.Binary,
    )
    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"],
        within=pyo.Reals,
    )

    model.assigned = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_rule(mdl, i):
        return sum(mdl.assigned[i, j] for j in mdl.cars) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_rule,
    )

    def car_rule(mdl, j):
        return sum(mdl.assigned[i, j] for i in mdl.participants) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_rule,
    )

    def preference_rule(mdl, i, j):
        return mdl.assigned[i, j] <= mdl.preference[i, j]

    model.preference_eligibility = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_value
        * sum(
            model.assigned[i, j]
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
        obj_val = float(pyo.value(model.total_assignment_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}