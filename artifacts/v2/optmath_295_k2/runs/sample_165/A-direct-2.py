import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    weight = params["objective_weight_per_assignment"]

    P = range(num_participants)
    C = range(num_cars)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(P, C, domain=pyo.Binary)

    # Disallow assignments to cars the participant is not interested in.
    model.allowed = pyo.Constraint(
        P, C,
        rule=lambda m, i, j: m.x[i, j] == 0 if preference_matrix[i][j] == 0 else pyo.Constraint.Skip,
    )

    # Each participant assigned to at most cap_participant cars.
    model.participant_cap = pyo.Constraint(
        P,
        rule=lambda m, i: sum(m.x[i, j] for j in C) <= cap_participant,
    )

    # Each car assigned to at most cap_car participants.
    model.car_cap = pyo.Constraint(
        C,
        rule=lambda m, j: sum(m.x[i, j] for i in P) <= cap_car,
    )

    model.obj = pyo.Objective(
        expr=sum(weight * model.x[i, j] for i in P for j in C),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}