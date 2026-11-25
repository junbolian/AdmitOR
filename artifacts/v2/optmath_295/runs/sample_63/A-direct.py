import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    num_participants = len(preference)
    num_cars = len(preference[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.x[i, j] for i in m.P for j in m.C)

    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= 1

    model.participant_constraint = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, j):
        return sum(m.x[i, j] for i in m.P) <= 1

    model.car_constraint = pyo.Constraint(model.C, rule=car_rule)

    def preference_rule(m, i, j):
        return m.x[i, j] <= preference[i][j]

    model.preference_constraint = pyo.Constraint(model.P, model.C, rule=preference_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.objective))

    return {"objective": obj_val, "status": "optimal"}