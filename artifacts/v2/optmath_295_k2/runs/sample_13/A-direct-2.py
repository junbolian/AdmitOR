import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    assignment_cap_per_participant = params["assignment_cap_per_participant"]
    assignment_cap_per_car = params["assignment_cap_per_car"]

    n_participants = len(preference_matrix)
    n_cars = len(preference_matrix[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(
            preference_matrix[i][j] * model.x[i, j]
            for i in model.P
            for j in model.C
        ),
        sense=pyo.maximize,
    )

    model.participant_cap = pyo.Constraint(
        model.P,
        rule=lambda m, i: sum(m.x[i, j] for j in m.C)
        <= assignment_cap_per_participant,
    )

    model.car_cap = pyo.Constraint(
        model.C,
        rule=lambda m, j: sum(m.x[i, j] for i in m.P) <= assignment_cap_per_car,
    )

    model.preference = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda m, i, j: m.x[i, j] <= preference_matrix[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}