# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5,6],"edges":[[0,0],[0,6],[1,5],[2,3],[2,6],[3,3],[3,6],[4,1],[4,2],[4,3],[5,1],[5,2],[5,4],[5,5]]},"params":{"preference[i,j]":"params[pref_i_j] for each edge","participant_capacity":"params[participant_capacity]","car_capacity":"params[car_capacity]","assignment_value":"params[assignment_value]"},"variables":{"assignment[i,j]":"Binary for each edge; unlisted pairs are forbidden"},"constraints":["For each participant i: sum(assignment[i,j] for incident edges) <= participant_capacity","For each car j: sum(assignment[i,j] for incident edges) <= car_capacity","For each edge (i,j): assignment[i,j] <= preference[i,j]"],"objective":"Maximize assignment_value * sum(assignment[i,j] for all edges)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 0), (0, 6),
        (1, 5),
        (2, 3), (2, 6),
        (3, 3), (3, 6),
        (4, 1), (4, 2), (4, 3),
        (5, 1), (5, 2), (5, 4), (5, 5),
    )

    preferences = {
        (0, 0): params["pref_0_0"],
        (0, 6): params["pref_0_6"],
        (1, 5): params["pref_1_5"],
        (2, 3): params["pref_2_3"],
        (2, 6): params["pref_2_6"],
        (3, 3): params["pref_3_3"],
        (3, 6): params["pref_3_6"],
        (4, 1): params["pref_4_1"],
        (4, 2): params["pref_4_2"],
        (4, 3): params["pref_4_3"],
        (5, 1): params["pref_5_1"],
        (5, 2): params["pref_5_2"],
        (5, 4): params["pref_5_4"],
        (5, 5): params["pref_5_5"],
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 6)
    model.edges = pyo.Set(dimen=2, initialize=edges)

    model.preference = pyo.Param(
        model.edges, initialize=preferences, within=pyo.Binary
    )
    model.participant_capacity = pyo.Param(
        initialize=params["participant_capacity"], within=pyo.Reals
    )
    model.car_capacity = pyo.Param(
        initialize=params["car_capacity"], within=pyo.Reals
    )
    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"], within=pyo.Reals
    )

    model.assignment = pyo.Var(model.edges, domain=pyo.Binary)

    def participant_limit_rule(instance, participant):
        return sum(
            instance.assignment[participant, car]
            for car in instance.cars
            if (participant, car) in instance.edges
        ) <= instance.participant_capacity

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(instance, car):
        return sum(
            instance.assignment[participant, car]
            for participant in instance.participants
            if (participant, car) in instance.edges
        ) <= instance.car_capacity

    model.car_limits = pyo.Constraint(model.cars, rule=car_limit_rule)

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limits = pyo.Constraint(
        model.edges, rule=preference_rule
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value * sum(
            model.assignment[participant, car]
            for participant, car in model.edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}