import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_participants = int(params["participants"])
    n_cars = int(params["cars"])
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference = params["preference"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)

    allowed = [
        (i, j)
        for i in range(n_participants)
        for j in range(n_cars)
        if preference[i][j] == 1
    ]
    model.AC = pyo.Set(initialize=allowed, dimen=2)

    model.x = pyo.Var(model.AC, domain=pyo.Binary)

    # Each participant assigned to at most participant_capacity cars
    def participant_rule(m, i):
        pairs = [(i, j) for j in range(n_cars) if (i, j) in m.AC]
        if not pairs:
            return pyo.Constraint.Feasible
        return pyo.quicksum(m.x[i, j] for (i, j) in pairs) <= participant_capacity

    model.participant_cap = pyo.Constraint(model.P, rule=participant_rule)

    # Each car assigned to at most car_capacity participants
    def car_rule(m, j):
        pairs = [(i, j) for i in range(n_participants) if (i, j) in m.AC]
        if not pairs:
            return pyo.Constraint.Feasible
        return pyo.quicksum(m.x[i, j] for (i, j) in pairs) <= car_capacity

    model.car_cap = pyo.Constraint(model.C, rule=car_rule)

    model.objective = pyo.Objective(
        expr=pyo.quicksum(model.x[i, j] for (i, j) in model.AC),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}