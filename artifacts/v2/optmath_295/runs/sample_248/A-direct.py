import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = params["preferences"]

    # Build set of allowed (participant, car) arcs
    allowed_arcs = [
        (p, c)
        for p in range(num_participants)
        for c in preferences[p]
        if 0 <= c < num_cars
    ]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=allowed_arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Each participant assigned to at most one car
    model.participant_cons = pyo.ConstraintList()
    for p in range(num_participants):
        arcs_for_p = [(pp, c) for (pp, c) in allowed_arcs if pp == p]
        if arcs_for_p:
            model.participant_cons.add(
                sum(model.x[a] for a in arcs_for_p) <= 1
            )

    # Each car assigned to at most one participant
    model.car_cons = pyo.ConstraintList()
    for c in range(num_cars):
        arcs_for_c = [(p, cc) for (p, cc) in allowed_arcs if cc == c]
        if arcs_for_c:
            model.car_cons.add(
                sum(model.x[a] for a in arcs_for_c) <= 1
            )

    model.objective = pyo.Objective(
        expr=sum(model.x[a] for a in model.arcs), sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}