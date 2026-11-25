import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]

    num_participants = len(preference)
    num_cars = len(preference[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            preference[p][c] * mdl.x[p, c]
            for p in mdl.P
            for c in mdl.C
        )

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(mdl, p):
        return sum(mdl.x[p, c] for c in mdl.C) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(mdl, c):
        return sum(mdl.x[p, c] for p in mdl.P) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    def valid_rule(mdl, p, c):
        if preference[p][c] == 0:
            return mdl.x[p, c] == 0
        return pyo.Constraint.Skip

    model.valid_con = pyo.Constraint(model.P, model.C, rule=valid_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))

    return {"objective": obj_val, "status": "optimal"}