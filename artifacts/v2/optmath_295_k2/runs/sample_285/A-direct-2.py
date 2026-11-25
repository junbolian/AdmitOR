import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]

    num_participants = len(preference)
    num_cars = len(preference[0])

    participant_set = list(range(num_participants))
    car_set = list(range(num_cars))

    model = pyo.ConcreteModel()

    model.pairs = pyo.Set(
        initialize=[(p, c) for p in participant_set for c in car_set if preference[p][c] == 1],
        dimen=2,
    )

    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    def participant_rule(m, p):
        terms = [m.x[p, c] for c in car_set if (p, c) in m.pairs]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    def car_rule(m, c):
        terms = [m.x[p, c] for p in participant_set if (p, c) in m.pairs]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_constraint = pyo.Constraint(participant_set, rule=participant_rule)
    model.car_constraint = pyo.Constraint(car_set, rule=car_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in model.pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}