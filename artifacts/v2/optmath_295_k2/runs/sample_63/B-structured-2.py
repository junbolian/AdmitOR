# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3]},"params":{"participant_car_interest_p0":"binary vector indexed by C","participant_car_interest_p1":"binary vector indexed by C","participant_car_interest_p2":"binary vector indexed by C","participant_car_interest_p3":"binary vector indexed by C","assignment_objective_coefficients":"scalar broadcast to all assignments, length-4 vector indexed by C and broadcast across P, flat length-16 vector in participant-major order, or 4x4 matrix indexed by P,C","participant_capacity":"scalar","car_capacity":"scalar"},"variables":{"x[p,c]":"binary"},"constraints":["x[p,c] <= interest[p,c] for all p in P,c in C","sum(x[p,c] for c in C) <= participant_capacity for all p in P","sum(x[p,c] for p in P) <= car_capacity for all c in C"],"objective":"maximize sum(weight[p,c]*x[p,c] for p in P,c in C)"}

from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    interest_rows = [
        params["participant_car_interest_p0"],
        params["participant_car_interest_p1"],
        params["participant_car_interest_p2"],
        params["participant_car_interest_p3"],
    ]
    coefficients = params["assignment_objective_coefficients"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    if isinstance(coefficients, Number):
        weights = {
            (participant, car): coefficients
            for participant in range(4)
            for car in range(4)
        }
    elif len(coefficients) == 16:
        weights = {
            (participant, car): coefficients[4 * participant + car]
            for participant in range(4)
            for car in range(4)
        }
    elif len(coefficients) == 4:
        if all(isinstance(value, Number) for value in coefficients):
            weights = {
                (participant, car): coefficients[car]
                for participant in range(4)
                for car in range(4)
            }
        else:
            if not all(len(row) == 4 for row in coefficients):
                raise ValueError(
                    "The assignment coefficient matrix must have shape 4x4."
                )
            weights = {
                (participant, car): coefficients[participant][car]
                for participant in range(4)
                for car in range(4)
            }
    else:
        raise ValueError(
            "assignment_objective_coefficients must be a scalar, "
            "a length-4 vector, a length-16 vector, or a 4x4 matrix."
        )

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 3)
    model.cars = pyo.RangeSet(0, 3)

    model.interest = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): interest_rows[participant][car]
            for participant in range(4)
            for car in range(4)
        },
        within=pyo.Binary,
    )
    model.assignment_weight = pyo.Param(
        model.participants,
        model.cars,
        initialize=weights,
        within=pyo.Reals,
    )
    model.participant_limit = pyo.Param(
        initialize=participant_capacity,
        within=pyo.Reals,
    )
    model.car_limit = pyo.Param(
        initialize=car_capacity,
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(mdl, participant, car):
        return mdl.x[participant, car] <= mdl.interest[participant, car]

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            sum(mdl.x[participant, car] for car in mdl.cars)
            <= mdl.participant_limit
        )

    model.participant_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return (
            sum(mdl.x[participant, car] for participant in mdl.participants)
            <= mdl.car_limit
        )

    model.car_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment_weight[participant, car] * model.x[participant, car]
            for participant in model.participants
            for car in model.cars
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}