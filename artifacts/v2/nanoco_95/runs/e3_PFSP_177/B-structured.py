# IR: {"sets":{"B":[0,1,2,3],"K":[0,1,2,3],"U":[0,1,2]},"params":{"processing_time[b,u]":"params['processing_time'][b][u], nonnegative; indices correspond to B0-B3 and U0-U2"},"variables":{"assigned[b,k]":"binary: batch b occupies sequence position k","completion[k,u]":"nonnegative continuous: completion time at position k on unit u"},"constraints":["Each batch occupies exactly one position: sum_k assigned[b,k] = 1.","Each position contains exactly one batch: sum_b assigned[b,k] = 1.","Define duration[k,u] = sum_b processing_time[b,u]*assigned[b,k].","Anchor the first operation: completion[0,0] = duration[0,0].","Unit availability for k>0: completion[k,u] >= completion[k-1,u] + duration[k,u].","Batch precedence for u>0: completion[k,u] >= completion[k,u-1] + duration[k,u]."],"objective":"Minimize completion[3,2], the campaign makespan."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the four-batch, three-unit permutation flow-shop problem.

    params["processing_time"][b][u] supplies the processing duration for
    batch Bb on unit Uu, using zero-based integer indices.
    """
    model = pyo.ConcreteModel()

    model.batches = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.units = pyo.RangeSet(0, 2)

    model.processing_duration = pyo.Param(
        model.batches,
        model.units,
        initialize={
            (batch, unit): params["processing_time"][batch][unit]
            for batch in model.batches
            for unit in model.units
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.batches,
        model.positions,
        domain=pyo.Binary,
    )
    model.completion = pyo.Var(
        model.positions,
        model.units,
        domain=pyo.NonNegativeReals,
    )

    def batch_assignment_rule(schedule, batch):
        return sum(
            schedule.assigned[batch, position]
            for position in schedule.positions
        ) == 1

    model.batch_assignment = pyo.Constraint(
        model.batches,
        rule=batch_assignment_rule,
    )

    def position_assignment_rule(schedule, position):
        return sum(
            schedule.assigned[batch, position]
            for batch in schedule.batches
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=position_assignment_rule,
    )

    def duration_rule(schedule, position, unit):
        return sum(
            schedule.processing_duration[batch, unit]
            * schedule.assigned[batch, position]
            for batch in schedule.batches
        )

    model.position_duration = pyo.Expression(
        model.positions,
        model.units,
        rule=duration_rule,
    )

    model.first_operation = pyo.Constraint(
        expr=model.completion[0, 0] == model.position_duration[0, 0]
    )

    def unit_availability_rule(schedule, position, unit):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            schedule.completion[position, unit]
            >= schedule.completion[position - 1, unit]
            + schedule.position_duration[position, unit]
        )

    model.unit_availability = pyo.Constraint(
        model.positions,
        model.units,
        rule=unit_availability_rule,
    )

    def batch_precedence_rule(schedule, position, unit):
        if unit == 0:
            return pyo.Constraint.Skip
        return (
            schedule.completion[position, unit]
            >= schedule.completion[position, unit - 1]
            + schedule.position_duration[position, unit]
        )

    model.batch_precedence = pyo.Constraint(
        model.positions,
        model.units,
        rule=batch_precedence_rule,
    )

    model.campaign_time = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.campaign_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}