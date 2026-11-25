import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_value = params["preference_edge_value"]

    participants = list(range(7))
    cars = list(range(5))

    preferences = {
        0: [],
        1: [1],
        2: [0, 3, 4],
        3: [0],
        4: [1, 3],
        5: [],
        6: [],
    }

    allowed_edges = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.E = pyo.Set(initialize=allowed_edges, dimen=2)

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def obj_rule(m):
        return sum(edge_value * m.x[p, c] for (p, c) in m.E)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        terms = [m.x[p, c] for c in cars if (p, c) in allowed_edges]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        terms = [m.x[p, c] for p in participants if (p, c) in allowed_edges]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}