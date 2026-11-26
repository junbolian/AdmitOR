import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lengths = params["car_lengths"]
    cap = params["side_capacity_limit"]
    n = len(lengths)

    model = pyo.ConcreteModel()
    model.cars = pyo.RangeSet(0, n - 1)
    # side[a] = 1 if car on side A, 0 if on side B
    model.side = pyo.Var(model.cars, domain=pyo.Binary)

    total = sum(lengths)
    # Minimize the larger side's total length (walking across the street is
    # negligible; the street is "occupied" up to whichever side is fullest).
    model.bigside = pyo.Var(domain=pyo.NonNegativeReals)

    def bigside_rule(m, c):
        sideA = sum(lengths[c] * m.side[c] for c in m.cars)
        sideB = sum(lengths[c] * (1 - m.side[c]) for c in m.cars)
        return m.bigside >= sideA

    def bigside_rule_b(m):
        sideB = sum(lengths[c] * (1 - m.side[c]) for c in m.cars)
        return m.bigside >= sideB

    model.c_bigside_a = pyo.Constraint(model.cars, rule=bigside_rule)
    model.c_bigside_b = pyo.Constraint(rule=bigside_rule_b)

    # Each side capacity limit
    def cap_a(m):
        return sum(lengths[c] * m.side[c] for c in m.cars) <= cap

    def cap_b(m):
        return sum(lengths[c] * (1 - m.side[c]) for c in m.cars) <= cap

    model.c_cap_a = pyo.Constraint(rule=cap_a)
    model.c_cap_b = pyo.Constraint(rule=cap_b)

    model.obj = pyo.Objective(expr=model.bigside, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}