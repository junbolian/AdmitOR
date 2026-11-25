import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    p0_4_interest = int(params["participant_0_4_interest"])
    p4_car1_interest = int(params["participant_4_car_1_interest"])
    p4_forbidden_interest = int(params["participant_4_forbidden_interest"])

    participants = range(num_participants)
    cars = range(num_cars)

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=list(participants))
    model.C = pyo.Set(initialize=list(cars))
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def interest(p, c):
        if p in (0, 1, 2, 3):
            return p0_4_interest
        if p == 4:
            if c == 1:
                return p4_car1_interest
            else:
                return 1 - p4_forbidden_interest
        return 0

    def rule_assign(m, p):
        return sum(m.x[p, c] for c in m.C) <= 1

    def rule_capacity(m, c):
        return sum(m.x[p, c] for p in m.P) <= 1

    def rule_interest(m, p, c):
        if interest(p, c) == 0:
            return m.x[p, c] == 0
        return pyo.Constraint.Skip

    model.assign = pyo.Constraint(model.P, rule=rule_assign)
    model.capacity = pyo.Constraint(model.C, rule=rule_capacity)
    model.interest_con = pyo.Constraint(model.P, model.C, rule=rule_interest)

    model.obj = pyo.Objective(
        expr=sum(
            interest(p, c) * model.x[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}