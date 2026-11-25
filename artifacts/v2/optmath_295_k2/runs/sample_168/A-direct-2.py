import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    p0_4_interest = int(params["participant_0_4_interest"])
    p4_car1_interest = int(params["participant_4_car_1_interest"])
    p4_forbidden_interest = int(params["participant_4_forbidden_interest"])

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    interest = {}
    for p in participants:
        for c in cars:
            interest[(p, c)] = 0

    for p in range(min(4, num_participants)):
        for c in cars:
            interest[(p, c)] = p0_4_interest

    if num_participants > 4:
        for c in cars:
            interest[(4, c)] = 0
        if num_cars > 1:
            interest[(4, 1)] = p4_car1_interest
        for c in cars:
            if c in (0, 2, 3) and p4_forbidden_interest:
                interest[(4, c)] = 1

    allowed_pairs = [(p, c) for p in participants for c in cars if interest[(p, c)] == 1]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participants, ordered=True)
    model.C = pyo.Set(initialize=cars, ordered=True)
    model.PC = pyo.Set(initialize=allowed_pairs, dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in m.PC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        return sum(m.x[pp, c] for (pp, c) in m.PC if pp == p) <= 1

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, cc] for (p, cc) in m.PC if cc == c) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}