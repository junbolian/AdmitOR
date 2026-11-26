# IR: {"sets":{"cars":"0..14","sides":"0..1"},"params":{"car_lengths":"15 nonnegative lengths from params","side_capacity_limit":"nonnegative capacity from params; None omits the capacity constraints"},"variables":{"park[cars,sides]":"Binary","occupied_length":"NonNegativeReals"},"constraints":["For each car i: sum_s park[i,s] = 1.","For each side s: sum_i car_lengths[i]*park[i,s] <= occupied_length.","If side_capacity_limit is not None, for each side s: sum_i car_lengths[i]*park[i,s] <= side_capacity_limit."],"objective":"Minimize occupied_length, the greater of the two occupied side lengths."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Use None for the original problem; supply the stated capacity for
    # the variant that limits the total car length on either side.
    car_lengths = list(params["car_lengths"])
    side_capacity_limit = params["side_capacity_limit"]

    if len(car_lengths) != 15:
        raise ValueError("car_lengths must contain exactly 15 entries.")

    model = pyo.ConcreteModel()

    model.cars = pyo.RangeSet(0, 14)
    model.sides = pyo.RangeSet(0, 1)

    model.car_length = pyo.Param(
        model.cars,
        initialize={
            car_idx: car_lengths[car_idx]
            for car_idx in range(15)
        },
        within=pyo.NonNegativeReals,
    )

    model.park = pyo.Var(
        model.cars,
        model.sides,
        domain=pyo.Binary,
    )
    model.occupied_length = pyo.Var(domain=pyo.NonNegativeReals)

    def assignment_rule(instance, car_idx):
        return sum(
            instance.park[car_idx, side_idx]
            for side_idx in instance.sides
        ) == 1

    model.car_assignment = pyo.Constraint(
        model.cars,
        rule=assignment_rule,
    )

    def occupied_length_rule(instance, side_idx):
        return sum(
            instance.car_length[car_idx] * instance.park[car_idx, side_idx]
            for car_idx in instance.cars
        ) <= instance.occupied_length

    model.side_extent = pyo.Constraint(
        model.sides,
        rule=occupied_length_rule,
    )

    if side_capacity_limit is not None:
        model.side_capacity = pyo.Param(
            initialize=side_capacity_limit,
            within=pyo.NonNegativeReals,
        )

        def capacity_rule(instance, side_idx):
            return sum(
                instance.car_length[car_idx]
                * instance.park[car_idx, side_idx]
                for car_idx in instance.cars
            ) <= instance.side_capacity

        model.side_capacity_constraints = pyo.Constraint(
            model.sides,
            rule=capacity_rule,
        )

    model.parking_objective = pyo.Objective(
        expr=model.occupied_length,
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Determine success solely by subsequent objective-value retrieval.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.parking_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}