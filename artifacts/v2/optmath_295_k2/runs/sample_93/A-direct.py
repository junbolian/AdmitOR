import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]

    num_participants = len(preferences)
    num_cars = len(preferences[0]) if num_participants > 0 else 0

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    allowed = [(i, j) for i in participants for j in cars if preferences[i][j] == 1]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(allowed, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(mdl.x[i, j] for (i, j) in allowed)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(mdl, i):
        terms = [mdl.x[i, j] for j in cars if (i, j) in allowed]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)

    def car_rule(mdl, j):
        terms = [mdl.x[i, j] for i in participants if (i, j) in allowed]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}