import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    assignment_value = params["assignment_value"]

    participants = ["participant_0", "participant_1", "participant_2", "participant_3"]
    cars = ["car_0", "car_1", "car_2", "car_3", "car_4"]

    preferences = {
        "participant_0": ["car_2", "car_4"],
        "participant_1": [],
        "participant_2": ["car_0", "car_4"],
        "participant_3": ["car_0", "car_4"],
    }

    allowed_pairs = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.A = pyo.Set(dimen=2, initialize=allowed_pairs)

    # Only create variables for allowed pairs; absent pairs are treated as 0.
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(model):
        return assignment_value * sum(model.x[p, c] for (p, c) in model.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(model, p):
        terms = [model.x[p, c] for c in preferences[p]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(model, c):
        terms = [model.x[p, c] for p in participants if c in preferences[p]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}