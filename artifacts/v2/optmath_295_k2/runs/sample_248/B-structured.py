# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])","A[p]":"car indices from participant p's preference parameter","D":"params['assignment_variable_domain'], interpreted as a binary domain"},"params":["participant_0_preferred_car_3","participant_1_preferred_car_1","participant_2_preferred_cars_1_3","participant_3_preferred_cars_2_4","participant_4_preferred_cars_3_5","participant_5_preferred_cars_2_6","participant_6_preferred_car_6","assignment_capacity_per_participant","assignment_capacity_per_car","num_participants","num_cars","assignment_variable_domain"],"variables":{"x[p,c]":"binary, with values restricted to D"},"constraints":["x[p,c] = 0 for every c not in A[p]","sum(c in C, x[p,c]) <= assignment_capacity_per_participant for every p in P","sum(p in P, x[p,c]) <= assignment_capacity_per_car for every c in C"],"objective":"maximize sum(p in P, c in C, x[p,c])"}

from numbers import Integral

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _car_indices(value):
    """Accept a scalar car index or an iterable of car indices."""
    if isinstance(value, Integral):
        return (value,)
    return tuple(value)


def solve(params):
    participant_count = params["num_participants"]
    car_count = params["num_cars"]
    participant_capacity = params["assignment_capacity_per_participant"]
    car_capacity = params["assignment_capacity_per_car"]
    domain_specification = params["assignment_variable_domain"]

    preferences = {
        0: _car_indices(params["participant_0_preferred_car_3"]),
        1: _car_indices(params["participant_1_preferred_car_1"]),
        2: _car_indices(params["participant_2_preferred_cars_1_3"]),
        3: _car_indices(params["participant_3_preferred_cars_2_4"]),
        4: _car_indices(params["participant_4_preferred_cars_3_5"]),
        5: _car_indices(params["participant_5_preferred_cars_2_6"]),
        6: _car_indices(params["participant_6_preferred_car_6"]),
    }

    # Accept the domain as "Binary", pyo.Binary, or an iterable such as [0, 1].
    if isinstance(domain_specification, str):
        if domain_specification.strip().lower() != "binary":
            return {"objective": None, "status": "invalid_binary_domain"}
        domain_values = tuple(pyo.Binary)
    else:
        domain_values = tuple(domain_specification)

    if not domain_values or any(
        value not in pyo.Binary for value in domain_values
    ):
        return {"objective": None, "status": "invalid_binary_domain"}

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(participant_count), ordered=True
    )
    model.cars = pyo.Set(initialize=range(car_count), ordered=True)
    model.assignment_values = pyo.Set(
        initialize=domain_values, within=pyo.Binary
    )
    model.allowed_cars = pyo.Set(
        model.participants,
        initialize=lambda mdl, participant: preferences.get(participant, ()),
    )

    model.participant_capacity = pyo.Param(initialize=participant_capacity)
    model.car_capacity = pyo.Param(initialize=car_capacity)

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=model.assignment_values,
    )

    def preference_rule(mdl, participant, car):
        if car in mdl.allowed_cars[participant]:
            return pyo.Constraint.Skip
        return mdl.assignment[participant, car] == 0

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    def participant_capacity_rule(mdl, participant):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car] for car in mdl.cars
            ),
            mdl.participant_capacity,
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(mdl, car):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            ),
            mdl.car_capacity,
        )

    model.car_limits = pyo.Constraint(
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

    # APPsi may raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval remains the sole success criterion.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}