import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Read problem data from params
    participants = params["participants"]
    cars = params["cars"]
    preferences = params["preferences"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)

    # Decision variables: binary assignment x[p, c]
    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Objective: maximize total number of successful assignments
    def obj_rule(m):
        return sum(m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Preference constraints: can only assign to a car the participant is interested in
    def pref_rule(m, p, c):
        if preferences[(p, c)] == 1:
            return pyo.Constraint.Skip
        return m.x[p, c] <= 0

    model.pref_con = pyo.Constraint(model.P, model.C, rule=pref_rule)

    # One car per participant
    def one_car_per_p(m, p):
        return sum(m.x[p, c] for c in m.C) <= 1

    model.one_car_per_p = pyo.Constraint(model.P, rule=one_car_per_p)

    # One participant per car
    def one_p_per_car(m, c):
        return sum(m.x[p, c] for p in m.P) <= 1

    model.one_p_per_car = pyo.Constraint(model.C, rule=one_p_per_car)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}