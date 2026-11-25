import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]

    preferences = {
        0: [int(params["participant_0_preferred_car_3"])],
        1: [int(params["participant_1_preferred_car_1"])],
        2: [int(v) for v in params["participant_2_preferred_cars_1_3"]],
        3: [int(v) for v in params["participant_3_preferred_cars_2_4"]],
        4: [int(v) for v in params["participant_4_preferred_cars_3_5"]],
        5: [int(v) for v in params["participant_5_preferred_cars_2_6"]],
        6: [int(params["participant_6_preferred_car_6"])],
    }

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    pairs = [
        (p, c)
        for p in participants
        for c in preferences.get(p, [])
        if 0 <= c < num_cars
    ]
    pair_set = set(pairs)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PC = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    model.total_assignments = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in pairs),
        sense=pyo.maximize,
    )

    def participant_rule(m, p):
        expr = sum(m.x[p, c] for c in cars if (p, c) in pair_set)
        if expr is 0:
            return pyo.Constraint.Skip
        return expr <= cap_participant

    def car_rule(m, c):
        expr = sum(m.x[p, c] for p in participants if (p, c) in pair_set)
        if expr is 0:
            return pyo.Constraint.Skip
        return expr <= cap_car

    model.participant_capacity = pyo.Constraint(model.P, rule=participant_rule)
    model.car_capacity = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}