import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    interest = params["participant_car_interest"]
    max_participant_assignments = params["max_participant_assignments"]
    max_car_assignments = params["max_car_assignments"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return pyo.summation(m.x)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def interest_rule(m, p, c):
        # can only assign to an interested car
        return m.x[p, c] <= interest[p][c]

    model.interest_con = pyo.Constraint(model.P, model.C, rule=interest_rule)

    def participant_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= max_participant_assignments

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        return sum(m.x[p, c] for p in m.P) <= max_car_assignments

    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}