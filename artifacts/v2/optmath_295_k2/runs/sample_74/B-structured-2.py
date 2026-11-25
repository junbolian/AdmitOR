# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":{"num_participants":"nonnegative integer","num_cars":"nonnegative integer","participant_car_interest":"binary matrix indexed by P,C","max_participant_assignments":"nonnegative integer","max_car_assignments":"nonnegative integer"},"variables":{"x[p,c]":"binary for p in P,c in C"},"constraints":["x[p,c] <= participant_car_interest[p][c] for p in P,c in C","sum(x[p,c] for c in C) <= max_participant_assignments for p in P","sum(x[p,c] for p in P) <= max_car_assignments for c in C"],"objective":"maximize sum(x[p,c] for p in P,c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    participant_car_interest = params["participant_car_interest"]
    max_participant_assignments = params["max_participant_assignments"]
    max_car_assignments = params["max_car_assignments"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.interest = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: (
            participant_car_interest[participant][car]
        ),
        within=pyo.Binary,
    )
    # Mutable parameters keep empty-sum constraints symbolic.
    model.participant_limit = pyo.Param(
        initialize=max_participant_assignments,
        within=pyo.NonNegativeIntegers,
        mutable=True,
    )
    model.car_limit = pyo.Param(
        initialize=max_car_assignments,
        within=pyo.NonNegativeIntegers,
        mutable=True,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def eligibility_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.interest[participant, car]
        )

    model.eligibility_constraints = pyo.Constraint(
        model.participants, model.cars, rule=eligibility_rule
    )

    def participant_capacity_rule(mdl, participant):
        return (
            pyo.quicksum(
                mdl.assignment[participant, car] for car in mdl.cars
            )
            <= mdl.participant_limit
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(mdl, car):
        return (
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            )
            <= mdl.car_limit
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
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