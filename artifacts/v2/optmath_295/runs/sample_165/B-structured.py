# IR: {"sets":{"participants":"range(participant_count)","cars":"range(car_count)"},"params":{"participant_count":"integer, frozen index-set size","car_count":"integer, frozen index-set size","participant_0_pref_car_1":"binary","participant_1_pref_car_5":"binary","participant_2_pref_car_3":"binary","participant_4_pref_car_1":"binary","participant_4_pref_car_4":"binary","participant_4_pref_car_5":"binary","participant_5_pref_car_4":"binary","preference[p,c]":"corresponding supplied preference; 0 for all unlisted pairs"},"variables":{"assignment[p,c]":"binary"},"constraints":["sum_c assignment[p,c] <= 1 for each participant p","sum_p assignment[p,c] <= 1 for each car c","assignment[p,c] <= preference[p,c] for every pair (p,c)"],"objective":"maximize sum_(p,c) assignment[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]

    preferences = {
        (0, 1): params["participant_0_pref_car_1"],
        (1, 5): params["participant_1_pref_car_5"],
        (2, 3): params["participant_2_pref_car_3"],
        (4, 1): params["participant_4_pref_car_1"],
        (4, 4): params["participant_4_pref_car_4"],
        (4, 5): params["participant_4_pref_car_5"],
        (5, 4): params["participant_5_pref_car_4"],
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(participant_count), ordered=True
    )
    model.cars = pyo.Set(initialize=range(car_count), ordered=True)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=preferences,
        default=0,
        within=pyo.Binary,
    )
    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_capacity_rule(mdl, participant):
        return sum(
            mdl.assignment[participant, car] for car in mdl.cars
        ) <= 1

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return sum(
            mdl.assignment[participant, car]
            for participant in mdl.participants
        ) <= 1

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    def preference_limit_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.preference_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}