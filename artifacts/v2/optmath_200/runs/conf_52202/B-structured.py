# IR: {"sets":{"participants":[0,1,2,3,4,5],"cars":[0,1,2,3,4,5],"allowed_pairs":[[0,0],[0,2],[0,4],[1,3],[2,0],[2,1],[2,3],[3,0],[3,1],[3,2],[4,3],[4,5],[5,1],[5,2],[5,3]]},"params":{"max_assignments_per_participant":"real, read from params","max_assignments_per_car":"real, read from params"},"variables":{"assignment[p,c]":"binary, defined only on allowed_pairs"},"constraints":["For each participant p: sum(assignment[p,c] for allowed cars c) <= max_assignments_per_participant","For each car c: sum(assignment[p,c] for allowed participants p) <= max_assignments_per_car","Preference rule: assignment variables exist only for allowed_pairs"],"objective":"maximize sum(assignment[p,c] for (p,c) in allowed_pairs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 5)
    model.allowed_pairs = pyo.Set(
        dimen=2,
        within=model.participants * model.cars,
        initialize=[
            (0, 0), (0, 2), (0, 4),
            (1, 3),
            (2, 0), (2, 1), (2, 3),
            (3, 0), (3, 1), (3, 2),
            (4, 3), (4, 5),
            (5, 1), (5, 2), (5, 3),
        ],
    )

    model.participant_limit = pyo.Param(
        initialize=params["max_assignments_per_participant"],
        within=pyo.Reals,
    )
    model.car_limit = pyo.Param(
        initialize=params["max_assignments_per_car"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(model.allowed_pairs, domain=pyo.Binary)

    def participant_capacity_rule(instance, participant):
        return (
            sum(
                instance.assignment[participant, car]
                for car in instance.cars
                if (participant, car) in instance.allowed_pairs
            )
            <= instance.participant_limit
        )

    def car_capacity_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
                if (participant, car) in instance.allowed_pairs
            )
            <= instance.car_limit
        )

    model.participant_capacity = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )
    model.car_capacity = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant, car in model.allowed_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors are allowed to propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}