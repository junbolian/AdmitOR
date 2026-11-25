import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    assignment_value = params["assignment_value"]

    n_participants = len(preference)
    n_cars = len(preference[0])

    pairs = [(i, j) for i in range(n_participants) for j in range(n_cars) if preference[i][j] == 1]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    def objective_rule(m):
        return sum(assignment_value * m.x[p] for p in m.pairs)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(m, i):
        terms = [m.x[i, j] for (pi, j) in m.pairs if pi == i]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, j):
        terms = [m.x[i, cj] for (i, cj) in m.pairs if cj == j]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}