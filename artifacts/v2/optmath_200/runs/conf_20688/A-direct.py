import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    participant_preferences = params["participant_preferences"]
    car_capacity = params["car_capacity"]
    participant_capacity = params["participant_capacity"]
    assignment_value = params["assignment_value"]

    n_participants = len(participant_preferences)
    n_cars = len(participant_preferences[0]) if n_participants > 0 else 0

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def car_cap_value(c):
        if isinstance(car_capacity, (list, tuple)):
            return car_capacity[c]
        return car_capacity

    def part_cap_value(p):
        if isinstance(participant_capacity, (list, tuple)):
            return participant_capacity[p]
        return participant_capacity

    def obj_rule(m):
        return sum(assignment_value * m.x[p, c] for p in m.P for c in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def pref_rule(m, p, c):
        if participant_preferences[p][c] == 0:
            return m.x[p, c] == 0
        return pyo.Constraint.Skip
    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    def part_cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= part_cap_value(p)
    model.part_cap_con = pyo.Constraint(model.P, rule=part_cap_rule)

    def car_cap_rule(m, c):
        return sum(m.x[p, c] for p in m.P) <= car_cap_value(c)
    model.car_cap_con = pyo.Constraint(model.C, rule=car_cap_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)}