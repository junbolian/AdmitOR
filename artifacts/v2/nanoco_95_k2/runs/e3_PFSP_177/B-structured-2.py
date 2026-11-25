# IR: {"sets":{"batches":[0,1,2,3],"positions":[0,1,2,3],"units":[0,1,2]},"params":{"proc_time":{"source":"params['proc_time']","indices":["batches","units"],"domain":"nonnegative real"}},"variables":{"assigned[b,k]":"binary","start_time[k,u]":"nonnegative real"},"expressions":{"duration[k,u]":"sum_b proc_time[b,u]*assigned[b,k]"},"constraints":["Each batch occupies exactly one position: sum_k assigned[b,k] = 1.","Each position contains exactly one batch: sum_b assigned[b,k] = 1.","Campaign begins at zero: start_time[0,0] = 0.","Workflow precedence for u > 0: start_time[k,u] >= start_time[k,u-1] + duration[k,u-1].","Common sequence and unit capacity for k > 0: start_time[k,u] >= start_time[k-1,u] + duration[k-1,u]."],"objective":"minimize start_time[3,2] + duration[3,2]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["proc_time"]

    model = pyo.ConcreteModel()

    model.batches = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.units = pyo.RangeSet(0, 2)

    model.proc_time = pyo.Param(
        model.batches,
        model.units,
        initialize={
            (batch, unit): processing_times[batch][unit]
            for batch in model.batches
            for unit in model.units
        },
        within=pyo.NonNegativeReals,
    )

    # The batch assigned to a position is identical across all units.
    model.assigned = pyo.Var(
        model.batches,
        model.positions,
        domain=pyo.Binary,
    )
    model.start_time = pyo.Var(
        model.positions,
        model.units,
        domain=pyo.NonNegativeReals,
    )

    def duration_rule(md, position, unit):
        return sum(
            md.proc_time[batch, unit] * md.assigned[batch, position]
            for batch in md.batches
        )

    model.duration = pyo.Expression(
        model.positions,
        model.units,
        rule=duration_rule,
    )

    def batch_assignment_rule(md, batch):
        return sum(
            md.assigned[batch, position] for position in md.positions
        ) == 1

    model.batch_assignment = pyo.Constraint(
        model.batches,
        rule=batch_assignment_rule,
    )

    def position_assignment_rule(md, position):
        return sum(
            md.assigned[batch, position] for batch in md.batches
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=position_assignment_rule,
    )

    model.campaign_origin = pyo.Constraint(
        expr=model.start_time[0, 0] == 0
    )

    def workflow_rule(md, position, unit):
        if unit == 0:
            return pyo.Constraint.Skip
        return (
            md.start_time[position, unit]
            >= md.start_time[position, unit - 1]
            + md.duration[position, unit - 1]
        )

    model.workflow_precedence = pyo.Constraint(
        model.positions,
        model.units,
        rule=workflow_rule,
    )

    def unit_capacity_rule(md, position, unit):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            md.start_time[position, unit]
            >= md.start_time[position - 1, unit]
            + md.duration[position - 1, unit]
        )

    model.unit_capacity = pyo.Constraint(
        model.positions,
        model.units,
        rule=unit_capacity_rule,
    )

    model.campaign_time = pyo.Objective(
        expr=model.start_time[3, 2] + model.duration[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.campaign_time))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}