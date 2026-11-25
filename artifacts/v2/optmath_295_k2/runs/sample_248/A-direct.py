import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    cap_participant = params["assignment_capacity_per_participant"]
    cap_car = params["assignment_capacity_per_car"]

    preferences = {
        0: [params["participant_0_preferred_car_3"]],
        1: [params["participant_1_preferred_car_1"]],
        2: list(params["participant_2_preferred_cars_1_3"]),
        3: list(params["participant_3_preferred_cars_2_4"]),
        4: list(params["participant_4_preferred_cars_3_5"]),
        5: list(params["participant_5_preferred_cars_2_6"]),
        6: [params["participant_6_preferred_car_6"]],
    }

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    allowed_pairs = [
        (p, c) for p in participants for c in preferences.get(p, []) if c in cars
    ]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PC = pyo.Set(initialize=allowed_pairs, dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    cars_by_participant = {p: [] for p in participants}
    participants_by_car = {c: [] for c in cars}
    for (p, c) in allowed_pairs:
        cars_by_participant[p].append(c)
        participants_by_car[c].append(p)

    def participant_rule(mm, p):
        return sum(mm.x[p, c] for c in cars_by_participant[p]) <= cap_participant

    def car_rule(mm, c):
        return sum(mm.x[p, c] for p in participants_by_car[c]) <= cap_car

    model.con_participant = pyo.Constraint(model.P, rule=participant_rule)
    model.con_car = pyo.Constraint(model.C, rule=car_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in allowed_pairs), sense=pyo.maximize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}