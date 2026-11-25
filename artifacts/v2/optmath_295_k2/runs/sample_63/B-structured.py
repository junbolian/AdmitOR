# IR: {"sets":{"participants":[0,1,2,3],"cars":[0,1,2,3]},"params":{"participant_car_interest_p0":"binary vector indexed by cars","participant_car_interest_p1":"binary vector indexed by cars","participant_car_interest_p2":"binary vector indexed by cars","participant_car_interest_p3":"binary vector indexed by cars","assignment_objective_coefficients":"uniform scalar, length-4 car-weight vector shared by participants, participant-major length-16 vector, or 4x4 matrix","participant_capacity":"nonnegative scalar","car_capacity":"nonnegative scalar"},"variables":{"assignment[p,c]":"binary"},"constraints":["assignment[p,c] <= interest[p,c] for each p,c","sum_c assignment[p,c] <= participant_capacity for each p","sum_p assignment[p,c] <= car_capacity for each c"],"objective":"maximize sum_{p,c} weight[p,c] * assignment[p,c]"}
from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    interests = [
        params["participant_car_interest_p0"],
        params["participant_car_interest_p1"],
        params["participant_car_interest_p2"],
        params["participant_car_interest_p3"],
    ]
    coefficients = params["assignment_objective_coefficients"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    def coefficient_at(participant, car):
        if isinstance(coefficients, Real):
            return coefficients

        if len(coefficients) == 16:
            return coefficients[participant * 4 + car]

        if len(coefficients) == 4:
            if isinstance(coefficients[0], Real):
                return coefficients[car]
            return coefficients[participant][car]

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
        initialize=lambda instance, participant, car: interests[participant][car],
        within=pyo.Binary,
    )
    model.assignment_weight = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda instance, participant, car: coefficient_at(
            participant, car
        ),
        within=pyo.Reals,
    )
    model.participant_limit = pyo.Param(
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.car_limit = pyo.Param(
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def preference_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.interest[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    def participant_capacity_rule(instance, participant):
        return (
            sum(
                instance.assignment[participant, car]
                for car in instance.cars
            )
            <= instance.participant_limit
        )

    model.participant_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= instance.car_limit
        )

    model.car_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment_weight[participant, car]
            * model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
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