# IR: {"sets":{"P":[0,1,2,3,4,5,6],"C":[0,1,2,3,4],"E":[[1,1],[2,0],[2,3],[2,4],[3,0],[4,1],[4,3]]},"params":{"preference_edge_value":"params['preference_edge_value']"},"variables":{"x[p,c]":{"index":"E","type":"binary"}},"constraints":["Preference: x exists only for (p,c) in E.","Participant capacity: sum(x[p,c] for c with (p,c) in E) <= 1 for each p in P.","Car capacity: sum(x[p,c] for p with (p,c) in E) <= 1 for each c in C."],"objective":"maximize preference_edge_value * sum(x[p,c] for (p,c) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=range(7), ordered=True)
    model.cars = pyo.Set(initialize=range(5), ordered=True)
    model.allowed_edges = pyo.Set(
        dimen=2,
        within=model.participants * model.cars,
        initialize=[
            (1, 1),
            (2, 0),
            (2, 3),
            (2, 4),
            (3, 0),
            (4, 1),
            (4, 3),
        ],
        ordered=True,
    )

    model.preference_edge_value = pyo.Param(
        initialize=params["preference_edge_value"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(model.allowed_edges, domain=pyo.Binary)

    def participant_capacity_rule(current_model, participant):
        assignments = pyo.quicksum(
            current_model.assignment[participant, car]
            for car in current_model.cars
            if (participant, car) in current_model.allowed_edges
        )
        return (None, assignments, 1)

    model.participant_capacity = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(current_model, car):
        assignments = pyo.quicksum(
            current_model.assignment[participant, car]
            for participant in current_model.participants
            if (participant, car) in current_model.allowed_edges
        )
        return (None, assignments, 1)

    model.car_capacity = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_preference_value = pyo.Objective(
        expr=model.preference_edge_value
        * pyo.quicksum(
            model.assignment[participant, car]
            for participant, car in model.allowed_edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_preference_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}