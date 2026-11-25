import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pref = params["preference_matrix"]
    unit_value = params["unit_assignment_value"]

    num_participants = len(pref)
    num_cars = len(pref[0]) if num_participants > 0 else 0

    eligible_pairs = [
        (p, c)
        for p in range(num_participants)
        for c in range(num_cars)
        if pref[p][c] == 1
    ]

    model = pyo.ConcreteModel()

    model.eligible = pyo.Set(initialize=eligible_pairs, dimen=2)
    model.participant_ids = pyo.RangeSet(0, num_participants - 1)
    model.car_ids = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.eligible, domain=pyo.Binary)

    def obj_rule(m):
        return unit_value * sum(m.x[p, c] for (p, c) in m.eligible)

    model.assignment_objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        terms = [m.x[p, c] for c in range(num_cars) if (p, c) in eligible_pairs]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_constraints = pyo.Constraint(
        model.participant_ids, rule=participant_rule
    )

    def car_rule(m, c):
        terms = [m.x[p, c] for p in range(num_participants) if (p, c) in eligible_pairs]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_constraints = pyo.Constraint(model.car_ids, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.assignment_objective))
    return {"objective": obj_val, "status": "optimal"}