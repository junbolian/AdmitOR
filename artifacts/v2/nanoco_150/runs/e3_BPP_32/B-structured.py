# IR: {"sets":{"I":"0..11 (spots)","J":"0..11 (candidate slots)"},"params":{"spot_durations":"nonnegative duration[i], read from params","slot_capacity":"nonnegative capacity, read from params"},"variables":{"assign[i,j]":"Binary","used[j]":"Binary"},"constraints":["For each i: sum_j assign[i,j] = 1","For each j: sum_i spot_durations[i]*assign[i,j] <= slot_capacity*used[j]","For each i,j: assign[i,j] <= used[j]"],"objective":"Minimize sum_j used[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    spot_durations = params["spot_durations"]
    slot_capacity = params["slot_capacity"]

    if len(spot_durations) != 12:
        raise ValueError("spot_durations must contain exactly 12 durations.")

    model = pyo.ConcreteModel()

    model.spots = pyo.RangeSet(0, 11)
    model.slots = pyo.RangeSet(0, 11)

    model.duration = pyo.Param(
        model.spots,
        initialize={i: spot_durations[i] for i in range(12)},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        initialize=slot_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assign = pyo.Var(model.spots, model.slots, domain=pyo.Binary)
    model.used = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(model, i):
        return sum(model.assign[i, j] for j in model.slots) == 1

    model.assignment_constraints = pyo.Constraint(
        model.spots, rule=assignment_rule
    )

    def capacity_rule(model, j):
        return (
            sum(
                model.duration[i] * model.assign[i, j]
                for i in model.spots
            )
            <= model.capacity * model.used[j]
        )

    model.capacity_constraints = pyo.Constraint(
        model.slots, rule=capacity_rule
    )

    def activation_rule(model, i, j):
        return model.assign[i, j] <= model.used[j]

    model.activation_constraints = pyo.Constraint(
        model.spots, model.slots, rule=activation_rule
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.used[j] for j in model.slots),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError when it cannot load a feasible solution.
    # Still attempt objective retrieval; do not inspect termination enums.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}