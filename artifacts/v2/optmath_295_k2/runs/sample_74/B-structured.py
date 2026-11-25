# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])"},"params":{"num_participants":"nonnegative integer","num_cars":"nonnegative integer","participant_car_interest":"binary matrix indexed by P,C","max_participant_assignments":"nonnegative integer","max_car_assignments":"nonnegative integer"},"variables":{"x[p,c]":"binary for p in P, c in C"},"constraints":["x[p,c] <= participant_car_interest[p][c] for all p,c","sum(x[p,c] for c in C) <= max_participant_assignments for all p","sum(x[p,c] for p in P) <= max_car_assignments for all c"],"objective":"maximize sum(x[p,c] for p in P, c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    participant_car_interest = params["participant_car_interest"]
    max_participant_assignments = params["max_participant_assignments"]
    max_car_assignments = params["max_car_assignments"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=range(num_participants), ordered=True)
    model.C = pyo.Set(initialize=range(num_cars), ordered=True)

    model.interest = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, p, c: participant_car_interest[p][c],
        within=pyo.Binary,
    )
    model.participant_limit = pyo.Param(
        initialize=max_participant_assignments,
        within=pyo.NonNegativeIntegers,
    )
    model.car_limit = pyo.Param(
        initialize=max_car_assignments,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def eligibility_rule(mdl, p, c):
        return mdl.x[p, c] <= mdl.interest[p, c]

    model.eligibility_constraints = pyo.Constraint(
        model.P, model.C, rule=eligibility_rule
    )

    def participant_capacity_rule(mdl, p):
        return (
            None,
            pyo.quicksum(mdl.x[p, c] for c in mdl.C),
            mdl.participant_limit,
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.P, rule=participant_capacity_rule
    )

    def car_capacity_rule(mdl, c):
        return (
            None,
            pyo.quicksum(mdl.x[p, c] for p in mdl.P),
            mdl.car_limit,
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.C, rule=car_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(model.x[p, c] for p in model.P for c in model.C),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}