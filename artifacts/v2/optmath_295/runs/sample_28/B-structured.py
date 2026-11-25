# IR: {"sets":{"participants":[0,1,2,3,4,5,6],"cars":[0,1,2,3,4,5],"preferred_pairs":[[0,2],[1,0],[2,0],[2,1],[3,1],[4,1],[6,3]]},"params":{"car_capacity":"params['car_capacity']","participant_assignment_limit":"params['participant_assignment_limit']"},"variables":{"assigned[p,c]":"binary, defined only for preferred_pairs"},"constraints":["For each participant p: sum(assigned[p,c] over preferred pairs containing p) <= participant_assignment_limit.","For each car c: sum(assigned[p,c] over preferred pairs containing c) <= car_capacity."],"objective":"maximize sum(assigned[p,c] over preferred_pairs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=range(7), ordered=True)
    model.cars = pyo.Set(initialize=range(6), ordered=True)
    model.preferred_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (0, 2),
            (1, 0),
            (2, 0),
            (2, 1),
            (3, 1),
            (4, 1),
            (6, 3),
        ],
        ordered=True,
    )

    model.car_capacity = pyo.Param(
        initialize=params["car_capacity"],
        within=pyo.Reals,
    )
    model.participant_assignment_limit = pyo.Param(
        initialize=params["participant_assignment_limit"],
        within=pyo.Reals,
    )

    model.assigned = pyo.Var(model.preferred_pairs, domain=pyo.Binary)

    def participant_bound_rule(instance, participant):
        return (
            None,
            pyo.quicksum(
                instance.assigned[participant_id, car_id]
                for participant_id, car_id in instance.preferred_pairs
                if participant_id == participant
            ),
            instance.participant_assignment_limit,
        )

    def car_bound_rule(instance, car):
        return (
            None,
            pyo.quicksum(
                instance.assigned[participant_id, car_id]
                for participant_id, car_id in instance.preferred_pairs
                if car_id == car
            ),
            instance.car_capacity,
        )

    model.participant_bounds = pyo.Constraint(
        model.participants,
        rule=participant_bound_rule,
    )
    model.car_bounds = pyo.Constraint(
        model.cars,
        rule=car_bound_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assigned[participant_id, car_id]
            for participant_id, car_id in model.preferred_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}