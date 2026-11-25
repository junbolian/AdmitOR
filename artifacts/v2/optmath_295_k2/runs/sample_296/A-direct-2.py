import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    n_participants = len(preferences)
    n_cars = len(preferences[0])

    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, n_participants - 1)
    model.cars = pyo.RangeSet(0, n_cars - 1)

    model.assign = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def objective_rule(m):
        return sum(
            preferences[i][j] * m.assign[i, j]
            for i in m.participants
            for j in m.cars
        )

    model.total_assignments = pyo.Objective(
        rule=objective_rule, sense=pyo.maximize
    )

    def participant_rule(m, i):
        return sum(m.assign[i, j] for j in m.cars) <= participant_capacity

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(m, j):
        return sum(m.assign[i, j] for i in m.participants) <= car_capacity

    model.car_limit = pyo.Constraint(model.cars, rule=car_rule)

    def preference_rule(m, i, j):
        return m.assign[i, j] <= preferences[i][j]

    model.preference_limit = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))

    return {"objective": obj_val, "status": "optimal"}