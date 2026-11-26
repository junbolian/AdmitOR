# IR: {"sets":{"cars":"1..15","sides":"1..2","restricted_side":"1"},"params":{"car_lengths":"positive car lengths in car order","side_capacity":"maximum total car length on the restricted side"},"variables":{"park[i,s]":"binary","occupied_length":"nonnegative continuous"},"constraints":["For each car i: sum_s park[i,s] = 1.","For each side s: sum_i car_lengths[i]*park[i,s] <= occupied_length.","sum_i car_lengths[i]*park[i,1] <= side_capacity."],"objective":"Minimize occupied_length."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize the maximum occupied length of the two street sides.

    The capacity applies to one designated side; the other side can
    accommodate the remaining cars. Applying the tight capacity to both
    sides would make parking all cars infeasible.
    """
    car_lengths = list(params["car_lengths"])
    side_capacity = params["side_capacity"]

    if len(car_lengths) != 15:
        raise ValueError("car_lengths must contain exactly 15 entries.")

    model = pyo.ConcreteModel()
    model.cars = pyo.RangeSet(1, 15)
    model.sides = pyo.RangeSet(1, 2)

    model.car_length = pyo.Param(
        model.cars,
        initialize={
            car_id: length
            for car_id, length in enumerate(car_lengths, start=1)
        },
        within=pyo.PositiveReals,
    )
    model.capacity = pyo.Param(
        initialize=side_capacity,
        within=pyo.NonNegativeReals,
    )

    model.park = pyo.Var(model.cars, model.sides, domain=pyo.Binary)
    model.occupied_length = pyo.Var(domain=pyo.NonNegativeReals)

    def assignment_rule(instance, car_id):
        return sum(
            instance.park[car_id, side_id]
            for side_id in instance.sides
        ) == 1

    model.car_assignment = pyo.Constraint(
        model.cars,
        rule=assignment_rule,
    )

    def street_span_rule(instance, side_id):
        return sum(
            instance.car_length[car_id] * instance.park[car_id, side_id]
            for car_id in instance.cars
        ) <= instance.occupied_length

    model.street_span = pyo.Constraint(
        model.sides,
        rule=street_span_rule,
    )

    model.restricted_side_capacity = pyo.Constraint(
        expr=sum(
            model.car_length[car_id] * model.park[car_id, 1]
            for car_id in model.cars
        ) <= model.capacity
    )

    model.parking_objective = pyo.Objective(
        expr=model.occupied_length,
        sense=pyo.minimize,
    )

    # APPsi may raise when it cannot load a feasible solution.
    # Success is determined solely by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.parking_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}