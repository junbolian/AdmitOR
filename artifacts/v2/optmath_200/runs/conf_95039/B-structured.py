# IR: {"sets":{"P":[0,1,2,3,4,5],"C":[0,1,2,3,4,5,6],"E":[[0,4],[0,6],[1,1],[1,5],[2,0],[2,2],[2,6],[3,1],[3,5],[4,4],[4,6],[5,0],[5,4],[5,5]]},"params":{"preference_i_j":"params['preference_i_j'] for (i,j) in E","participant_capacity":"params['participant_capacity']","car_capacity":"params['car_capacity']"},"variables":{"x[i,j]":"Binary for (i,j) in E; assignments outside E are excluded"},"constraints":["x[i,j] <= preference_i_j for (i,j) in E","sum(x[i,j] for j with (i,j) in E) <= participant_capacity for i in P","sum(x[i,j] for i with (i,j) in E) <= car_capacity for j in C"],"objective":"maximize sum(x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 4), (0, 6),
        (1, 1), (1, 5),
        (2, 0), (2, 2), (2, 6),
        (3, 1), (3, 5),
        (4, 4), (4, 6),
        (5, 0), (5, 4), (5, 5),
    )
    preferences = {
        (i, j): params[f"preference_{i}_{j}"]
        for i, j in edges
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 5)
    model.cars = pyo.RangeSet(0, 6)
    model.edges = pyo.Set(dimen=2, initialize=edges)

    model.preference = pyo.Param(model.edges, initialize=preferences)
    model.participant_capacity = pyo.Param(
        initialize=params["participant_capacity"]
    )
    model.car_capacity = pyo.Param(
        initialize=params["car_capacity"]
    )

    model.assignment = pyo.Var(model.edges, domain=pyo.Binary)

    def preference_rule(instance, i, j):
        return instance.assignment[i, j] <= instance.preference[i, j]

    model.preference_limits = pyo.Constraint(
        model.edges, rule=preference_rule
    )

    def participant_rule(instance, i):
        total = sum(
            instance.assignment[i, j]
            for participant, j in edges
            if participant == i
        )
        return (None, total, instance.participant_capacity)

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_rule
    )

    def car_rule(instance, j):
        total = sum(
            instance.assignment[i, j]
            for i, car in edges
            if car == j
        )
        # Tuple form remains a valid constraint when the sum is empty.
        return (None, total, instance.car_capacity)

    model.car_limits = pyo.Constraint(model.cars, rule=car_rule)

    model.total_assignments = pyo.Objective(
        expr=sum(model.assignment[i, j] for i, j in edges),
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