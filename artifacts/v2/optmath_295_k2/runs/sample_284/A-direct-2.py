import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    n_participants = len(preferences)
    n_cars = len(preferences[0])

    participants = list(range(n_participants))
    cars = list(range(n_cars))

    model = pyo.ConcreteModel()

    model.assign = pyo.Var(participants, cars, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.assign[p, c] for p in participants for c in cars)

    model.total_assignments = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def preference_rule(m, p, c):
        if preferences[p][c] == 0:
            return m.assign[p, c] <= 0
        return pyo.Constraint.Skip

    model.preference_con = pyo.Constraint(participants, cars, rule=preference_rule)

    def one_car_per_participant_rule(m, p):
        return sum(m.assign[p, c] for c in cars) <= 1

    model.one_car_per_participant = pyo.Constraint(participants, rule=one_car_per_participant_rule)

    def one_participant_per_car_rule(m, c):
        return sum(m.assign[p, c] for p in participants) <= 1

    model.one_participant_per_car = pyo.Constraint(cars, rule=one_participant_per_car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}