import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference_matrix = params["preference_matrix"]

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Objective: maximize total assignments weighted by assignment_value
    model.obj = pyo.Objective(
        expr=sum(
            assignment_value * model.x[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.maximize,
    )

    # Eligibility: cannot assign to a car the participant is not interested in
    def eligibility_rule(model, p, c):
        return model.x[p, c] <= preference_matrix[p][c]

    model.eligibility_con = pyo.Constraint(model.P, model.C, rule=eligibility_rule)

    # Each participant at most participant_capacity cars
    def participant_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= participant_capacity

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    # Each car at most car_capacity participants
    def car_rule(model, c):
        return sum(model.x[p, c] for p in model.P) <= car_capacity

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}