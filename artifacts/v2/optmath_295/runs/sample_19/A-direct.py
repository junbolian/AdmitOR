import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    preference_weights = params["preference_weights"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    # preference_weights may be a flat list of length num_participants*num_cars,
    # or a nested list of length num_participants (each row length num_cars).
    if len(preference_weights) == num_participants and all(
        hasattr(row, "__len__") for row in preference_weights
    ):
        def weight(p, c):
            return preference_weights[p][c]
    else:
        def weight(p, c):
            return preference_weights[p * num_cars + c]

    editable_edges = [
        (p, c)
        for p in participants
        for c in cars
        if weight(p, c) != 0
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.E = pyo.Set(initialize=editable_edges, dimen=2)

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def objective_rule(m):
        return sum(assignment_value * m.x[p, c] for (p, c) in m.E)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in m.C if (p, c) in m.E) <= participant_capacity

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in m.P if (p, c) in m.E) <= car_capacity

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}