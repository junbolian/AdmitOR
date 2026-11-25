import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_participants = int(params["participant_count"])
    n_cars = int(params["car_count"])
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    P = range(n_participants)
    C = range(n_cars)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(p, c) for p in P for c in C if preference[p][c] == 1],
        domain=pyo.Binary,
    )

    def obj_rule(m):
        return sum(assignment_value * m.x[p, c] for (p, c) in m.x)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in C if (p, c) in m.x) <= participant_capacity

    model.participant_limit = pyo.Constraint(P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in P if (p, c) in m.x) <= car_capacity

    model.car_limit = pyo.Constraint(C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}