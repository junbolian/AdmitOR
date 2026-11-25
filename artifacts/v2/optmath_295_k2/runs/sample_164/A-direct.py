import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = int(params["participant_count"])
    car_count = int(params["car_count"])
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = float(params["assignment_value"])

    participants = range(participant_count)
    cars = range(car_count)

    pref = {}
    for i in participants:
        row = preference[i]
        for j in cars:
            pref[(i, j)] = int(row[j])

    allowed = [(i, j) for i in participants for j in cars if pref[(i, j)] == 1]

    pc = {}
    for i in participants:
        if isinstance(participant_capacity, (list, tuple)):
            pc[i] = int(participant_capacity[i])
        else:
            pc[i] = int(participant_capacity)

    cc = {}
    for j in cars:
        if isinstance(car_capacity, (list, tuple)):
            cc[j] = int(car_capacity[j])
        else:
            cc[j] = int(car_capacity)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, participant_count - 1)
    model.C = pyo.RangeSet(0, car_count - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def objective_rule(m):
        return sum(assignment_value * m.x[i, j] for (i, j) in allowed)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(m, i):
        return sum(m.x[i, j] for j in cars) <= pc[i]

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, j):
        return sum(m.x[i, j] for i in participants) <= cc[j]

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    def pref_rule(m, i, j):
        if pref[(i, j)] == 0:
            return m.x[i, j] == 0
        return pyo.Constraint.Skip

    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}