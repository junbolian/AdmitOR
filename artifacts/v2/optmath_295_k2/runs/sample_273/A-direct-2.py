import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    n_participants = len(preference)
    n_cars = len(preference[0]) if n_participants > 0 else 0

    participants = list(range(n_participants))
    cars = list(range(n_cars))

    model = pyo.ConcreteModel()

    allowed_pairs = [(p, c) for p in participants for c in cars if preference[p][c] == 1]

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PC = pyo.Set(initialize=allowed_pairs, dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    def objective_rule(m):
        return sum(assignment_value * m.x[p, c] for (p, c) in allowed_pairs)

    model.total_value = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in cars if (p, c) in model.PC) <= participant_capacity[p]

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in participants if (p, c) in model.PC) <= car_capacity[c]

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}