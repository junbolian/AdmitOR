import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pref = params["preference_matrix"]
    unit_value = params["unit_assignment_value"]

    num_participants = len(pref)
    num_cars = len(pref[0])

    participants = range(num_participants)
    cars = range(num_cars)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(participants))
    model.C = pyo.Set(initialize=list(cars))

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Preference constraints: cannot assign p to c if pref[p][c] == 0
    def pref_rule(model, p, c):
        if pref[p][c] == 0:
            return model.x[p, c] == 0
        return pyo.Constraint.Skip

    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    # Each participant assigned to at most one car
    def part_rule(model, p):
        return sum(model.x[p, c] for c in model.C) <= 1

    model.part_con = pyo.Constraint(model.P, rule=part_rule)

    # Each car assigned to at most one participant
    def car_rule(model, c):
        return sum(model.x[p, c] for p in model.P) <= 1

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    # Objective: maximize total assigned value using the provided unit value
    def obj_rule(model):
        return sum(unit_value * model.x[p, c] for p in model.P for c in model.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}