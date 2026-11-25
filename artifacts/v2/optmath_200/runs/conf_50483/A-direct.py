import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_preferences = params["participant_preferences"]
    max_assignments_per_participant = params["max_assignments_per_participant"]
    max_participants_per_car = params["max_participants_per_car"]
    objective_coefficients = params["objective_coefficients"]

    participants = list(range(len(participant_preferences)))
    cars = list(range(len(participant_preferences[0])))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)

    model.assign = pyo.Var(model.P, model.C, within=pyo.Binary)

    def obj_rule(model):
        return sum(
            objective_coefficients[i][j] * model.assign[i, j]
            for i in model.P
            for j in model.C
        )

    model.total_reward = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def preference_rule(model, i, j):
        if participant_preferences[i][j] == 0:
            return model.assign[i, j] == 0
        return pyo.Constraint.Skip

    model.preference_con = pyo.Constraint(model.P, model.C, rule=preference_rule)

    def participant_cap_rule(model, i):
        return sum(model.assign[i, j] for j in model.C) <= max_assignments_per_participant[i]

    model.participant_cap = pyo.Constraint(model.P, rule=participant_cap_rule)

    def car_cap_rule(model, j):
        return sum(model.assign[i, j] for i in model.P) <= max_participants_per_car[j]

    model.car_cap = pyo.Constraint(model.C, rule=car_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_reward))
    return {"objective": obj_val, "status": "optimal"}