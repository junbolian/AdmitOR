import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    max_part = params["max_assignments_per_participant"]
    max_car = params["max_assignments_per_car"]

    participants = list(range(6))
    cars = list(range(6))

    preferences = {
        0: [0, 2, 4],
        1: [3],
        2: [0, 1, 3],
        3: [0, 1, 2],
        4: [3, 5],
        5: [1, 2, 3],
    }

    arcs = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.A = pyo.Set(dimen=2, initialize=arcs)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def part_rule(m, p):
        return sum(m.x[p, c] for c in preferences[p] if (p, c) in m.A) <= max_part

    model.part_con = pyo.Constraint(model.P, rule=part_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in participants if (p, c) in m.A) <= max_car

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}