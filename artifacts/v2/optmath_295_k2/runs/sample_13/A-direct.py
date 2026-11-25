import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pref = params["preference_matrix"]
    part_cap = params["assignment_cap_per_participant"]
    car_cap = params["assignment_cap_per_car"]

    n_part = len(pref)
    n_car = len(pref[0]) if n_part > 0 else 0

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_part - 1)
    model.C = pyo.RangeSet(0, n_car - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(pref[i][j] * m.x[i, j] for i in m.P for j in m.C)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def part_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= part_cap

    model.part_limit = pyo.Constraint(model.P, rule=part_rule)

    def car_rule(m, j):
        return sum(m.x[i, j] for i in m.P) <= car_cap

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    def pref_rule(m, i, j):
        if pref[i][j] == 1:
            return pyo.Constraint.Skip
        return m.x[i, j] == 0

    model.pref_limit = pyo.Constraint(model.P, model.C, rule=pref_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}