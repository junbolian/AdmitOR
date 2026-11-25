import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    obj_coef = params["objective_coefficient"]

    participants = list(range(7))
    cars = list(range(8))

    preferences = {
        0: [1, 6, 7],
        1: [3],
        2: [1, 2, 4],
        3: [0],
        4: [2, 4, 5],
        5: [],
        6: [0, 1, 2, 3, 5],
    }

    valid_pairs = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(valid_pairs, domain=pyo.Binary)

    model.participant_constraint = pyo.Constraint(
        participants,
        rule=lambda mdl, p: (
            sum(mdl.x[p, c] for c in preferences[p]) <= 1
            if preferences[p]
            else pyo.Constraint.Feasible
        ),
    )

    model.car_constraint = pyo.Constraint(
        cars,
        rule=lambda mdl, c: (
            sum(
                mdl.x[p, c] for p in participants if c in preferences[p]
            )
            <= 1
        ),
    )

    model.objective = pyo.Objective(
        expr=sum(obj_coef * model.x[p, c] for (p, c) in valid_pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}