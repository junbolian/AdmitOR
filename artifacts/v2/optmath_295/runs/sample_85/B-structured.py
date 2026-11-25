# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])"},"params":{"preferences":"Specified (i,j) entries read params['pref_i_j']; all other entries are structural zeros","pref_4_none":"Optional empty-row marker: read params['pref_4_none'] when present and require zero; absence leaves row 4 structurally zero","participant_capacity":"params['participant_capacity']","car_capacity":"params['car_capacity']","num_participants":"params['num_participants']; frozen at 6","num_cars":"params['num_cars']; frozen at 6","assignment_coefficient":"params['assignment_coefficient']"},"variables":{"assignment[p,c]":"Binary"},"constraints":["sum(assignment[p,c] for c in C) <= participant_capacity for each p in P","sum(assignment[p,c] for p in P) <= car_capacity for each c in C","assignment[p,c] <= preferences[p,c] for each (p,c) in P x C"],"objective":{"sense":"maximize","expression":"assignment_coefficient * sum(assignment[p,c] for p in P for c in C)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_coefficient = params["assignment_coefficient"]

    preference_data = {
        (0, 2): params["pref_0_2"],
        (0, 5): params["pref_0_5"],
        (1, 0): params["pref_1_0"],
        (1, 1): params["pref_1_1"],
        (1, 3): params["pref_1_3"],
        (2, 0): params["pref_2_0"],
        (2, 2): params["pref_2_2"],
        (3, 1): params["pref_3_1"],
        (3, 3): params["pref_3_3"],
        (3, 4): params["pref_3_4"],
        (5, 0): params["pref_5_0"],
        (5, 3): params["pref_5_3"],
    }

    if num_participants != 6 or num_cars != 6:
        return {"objective": None, "status": "invalid_dimensions"}

    # Participant 4's row is structurally zero. Some callers omit its
    # redundant marker; when supplied, read and validate it explicitly.
    if "pref_4_none" in params:
        pref_4_none = params["pref_4_none"]
        if pref_4_none != 0:
            return {"objective": None, "status": "invalid_empty_preference_row"}
        for car in range(num_cars):
            preference_data[(4, car)] = pref_4_none

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants),
        ordered=True,
    )
    model.cars = pyo.Set(
        initialize=range(num_cars),
        ordered=True,
    )

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=preference_data,
        default=0,
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )
    model.assignment_coefficient = pyo.Param(
        initialize=assignment_coefficient,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(instance, participant):
        return (
            sum(instance.assignment[participant, car] for car in instance.cars)
            <= instance.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= instance.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    def preference_limit_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preference[participant, car]
        )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_limit_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=model.assignment_coefficient
        * sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}