import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]

    n_participants = len(preference)
    n_cars = len(preference[0])

    participants = list(range(n_participants))
    cars = list(range(n_cars))

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=participants)
    model.cars = pyo.Set(initialize=cars)
    model.assignments = pyo.Set(
        initialize=[(p, c) for p in participants for c in cars],
        dimen=2,
    )

    model.x = pyo.Var(model.assignments, domain=pyo.Binary)

    # Fix x to zero where preference is 0
    for p in participants:
        for c in cars:
            if preference[p][c] == 0:
                model.x[p, c].fix(0)

    def objective_rule(m):
        return assignment_value * sum(
            m.x[p, c]
            for p in participants
            for c in cars
            if preference[p][c] == 1
        )

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_capacity_rule(m, p):
        return sum(m.x[p, c] for c in cars) <= participant_capacity

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(m, c):
        return sum(m.x[p, c] for p in participants) <= car_capacity

    model.car_limit = pyo.Constraint(model.cars, rule=car_capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}