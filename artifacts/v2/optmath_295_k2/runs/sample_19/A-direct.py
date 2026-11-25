import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    preferences = {}
    for p in range(num_participants):
        preferences[p] = list(params["preference_p" + str(p)])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    # x[p, c] = 1 iff participant p assigned to car c
    car_pairs = [(p, c) for p in range(num_participants) for c in preferences[p]]
    model.pairs = pyo.Set(initialize=car_pairs, dimen=2)
    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    # Objective: maximize number of successful assignments
    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in car_pairs),
        sense=pyo.maximize,
    )

    # Each participant at most one car
    model.participant_constraint = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[p, c] for c in preferences[p]) <= 1,
    )

    # Each car at most one participant
    model.car_constraint = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(
            m.x[p, c] for p in range(num_participants) if c in preferences[p]
        ) <= 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}