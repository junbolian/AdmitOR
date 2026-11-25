import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference_matrix = params["preference_matrix"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = len(preference_matrix)
    num_cars = len(preference_matrix[0])

    participants = range(num_participants)
    cars = range(num_cars)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(i, j) for i in participants for j in cars],
        domain=pyo.Binary,
    )

    model.assignment = pyo.Objective(
        expr=sum(
            model.x[i, j] for i in participants for j in cars
        ),
        sense=pyo.maximize,
    )

    def preference_rule(mdl, i, j):
        return mdl.x[i, j] <= preference_matrix[i][j]

    model.preference_constraint = pyo.Constraint(
        [(i, j) for i in participants for j in cars],
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cars) <= participant_capacity[i]

    model.participant_capacity_constraint = pyo.Constraint(
        participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(mdl, j):
        return sum(mdl.x[i, j] for i in participants) <= car_capacity[j]

    model.car_capacity_constraint = pyo.Constraint(
        cars, rule=car_capacity_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.assignment))
    return {"objective": obj_val, "status": "optimal"}