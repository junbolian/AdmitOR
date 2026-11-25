import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = 4
    num_cars = 4

    interest = {
        0: params["participant_car_interest_p0"],
        1: params["participant_car_interest_p1"],
        2: params["participant_car_interest_p2"],
        3: params["participant_car_interest_p3"],
    }

    weights = params["assignment_objective_coefficients"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    def weight_at(p, c):
        return weights[p * num_cars + c] if isinstance(weights, (list, tuple)) else weights

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            weight_at(p, c) * mdl.x[p, c]
            for p in mdl.P
            for c in mdl.C
        )

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(mdl, p):
        return sum(mdl.x[p, c] for c in mdl.C) <= participant_capacity

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(mdl, c):
        return sum(mdl.x[p, c] for p in mdl.P) <= car_capacity

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    def interest_rule(mdl, p, c):
        return mdl.x[p, c] <= interest[p][c]

    model.interest_limit = pyo.Constraint(model.P, model.C, rule=interest_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}