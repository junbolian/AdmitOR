import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference_matrix"]
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    weight = params["objective_weight_per_assignment"]

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(participants, cars, domain=pyo.Binary)

    # Only allow assignment where a preference exists
    model.allowed = pyo.ConstraintList()
    for i in participants:
        for j in cars:
            if not preference[i][j]:
                model.allowed.add(model.assign[i, j] == 0)

    # Capacity per participant
    model.participant_cap = pyo.Constraint(
        participants,
        rule=lambda m, i: sum(m.assign[i, j] for j in cars) <= cap_participant,
    )

    # Capacity per car
    model.car_cap = pyo.Constraint(
        cars,
        rule=lambda m, j: sum(m.assign[i, j] for i in participants) <= cap_car,
    )

    # Objective: maximize weighted assignments
    model.objective_expression = pyo.Objective(
        expr=sum(weight * model.assign[i, j] for i in participants for j in cars),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective_expression))
    return {"objective": obj_val, "status": "optimal"}