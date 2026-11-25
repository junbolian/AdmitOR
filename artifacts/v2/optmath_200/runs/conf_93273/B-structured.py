# IR: {"sets":{"participants":"0..6","cars":"0..6"},"params":{"assignment_value":"params[assignment_value]","eligibility":"params[participant_i_pref_car_j] for listed pairs; structural zero otherwise","listed_pairs":[[0,0],[0,5],[0,6],[2,1],[2,3],[2,6],[3,1],[3,5],[3,6],[4,3],[5,0],[5,6],[6,0]],"participant_capacity":"params[participant_capacity]","car_capacity":"params[car_capacity]"},"variables":{"x[i,j]":"Binary for all participants i and cars j"},"constraints":["x[i,j] <= eligibility[i,j] for all i,j","sum_j x[i,j] <= participant_capacity for all i","sum_i x[i,j] <= car_capacity for all j"],"objective":"maximize assignment_value * sum_{i,j} x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    eligibility = {
        (0, 0): params["participant_0_pref_car_0"],
        (0, 5): params["participant_0_pref_car_5"],
        (0, 6): params["participant_0_pref_car_6"],
        (2, 1): params["participant_2_pref_car_1"],
        (2, 3): params["participant_2_pref_car_3"],
        (2, 6): params["participant_2_pref_car_6"],
        (3, 1): params["participant_3_pref_car_1"],
        (3, 5): params["participant_3_pref_car_5"],
        (3, 6): params["participant_3_pref_car_6"],
        (4, 3): params["participant_4_pref_car_3"],
        (5, 0): params["participant_5_pref_car_0"],
        (5, 6): params["participant_5_pref_car_6"],
        (6, 0): params["participant_6_pref_car_0"],
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 6)
    model.cars = pyo.RangeSet(0, 6)

    model.assignment_value = pyo.Param(
        initialize=params["assignment_value"], within=pyo.Reals
    )
    model.participant_capacity = pyo.Param(
        initialize=params["participant_capacity"], within=pyo.Reals
    )
    model.car_capacity = pyo.Param(
        initialize=params["car_capacity"], within=pyo.Reals
    )
    model.eligibility = pyo.Param(
        model.participants,
        model.cars,
        initialize=eligibility,
        default=0,
        within=pyo.Binary,
    )

    model.x = pyo.Var(model.participants, model.cars, domain=pyo.Binary)

    def eligibility_rule(instance, participant, car):
        return instance.x[participant, car] <= instance.eligibility[participant, car]

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=eligibility_rule
    )

    def participant_capacity_rule(instance, participant):
        return (
            sum(instance.x[participant, car] for car in instance.cars)
            <= instance.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(instance, car):
        return (
            sum(
                instance.x[participant, car]
                for participant in instance.participants
            )
            <= instance.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * sum(
            model.x[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}