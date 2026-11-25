# IR: {"sets":{"batches":[0,1,2,3],"positions":[0,1,2,3],"units":[0,1,2]},"params":{"proc_time":"nonnegative processing times indexed by [batch][unit]"},"variables":{"assigned[batch,position]":"binary","start[position,unit]":"nonnegative continuous"},"expressions":{"duration[position,unit]":"sum(proc_time[batch,unit]*assigned[batch,position] for batch in batches)"},"constraints":["Each batch occupies exactly one position: sum(assigned[batch,position] for position in positions)=1.","Each position contains exactly one batch: sum(assigned[batch,position] for batch in batches)=1.","The first batch starts immediately: start[0,0]=0.","Workflow precedence for unit>0: start[position,unit]>=start[position,unit-1]+duration[position,unit-1].","Common sequence and unit capacity for position>0: start[position,unit]>=start[position-1,unit]+duration[position-1,unit]."],"objective":"minimize start[3,2]+duration[3,2]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proc_time = params["proc_time"]

    model = pyo.ConcreteModel()
    model.batches = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.units = pyo.RangeSet(0, 2)

    model.processing_duration = pyo.Param(
        model.batches,
        model.units,
        initialize=lambda model, batch, unit: proc_time[batch][unit],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.batches,
        model.positions,
        domain=pyo.Binary,
    )
    model.start = pyo.Var(
        model.positions,
        model.units,
        domain=pyo.NonNegativeReals,
    )

    def duration_rule(model, position, unit):
        return sum(
            model.processing_duration[batch, unit]
            * model.assigned[batch, position]
            for batch in model.batches
        )

    model.duration = pyo.Expression(
        model.positions,
        model.units,
        rule=duration_rule,
    )

    def batch_assignment_rule(model, batch):
        return sum(
            model.assigned[batch, position]
            for position in model.positions
        ) == 1

    model.batch_assignment = pyo.Constraint(
        model.batches,
        rule=batch_assignment_rule,
    )

    def position_assignment_rule(model, position):
        return sum(
            model.assigned[batch, position]
            for batch in model.batches
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=position_assignment_rule,
    )

    model.campaign_origin = pyo.Constraint(expr=model.start[0, 0] == 0)

    def workflow_rule(model, position, unit):
        if unit == 0:
            return pyo.Constraint.Skip
        return (
            model.start[position, unit]
            >= model.start[position, unit - 1]
            + model.duration[position, unit - 1]
        )

    model.workflow_precedence = pyo.Constraint(
        model.positions,
        model.units,
        rule=workflow_rule,
    )

    def sequence_rule(model, position, unit):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            model.start[position, unit]
            >= model.start[position - 1, unit]
            + model.duration[position - 1, unit]
        )

    model.unit_sequence = pyo.Constraint(
        model.positions,
        model.units,
        rule=sequence_rule,
    )

    model.campaign_time = pyo.Objective(
        expr=model.start[3, 2] + model.duration[3, 2],
        sense=pyo.minimize,
    )

    # APPsi may raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines whether to report success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.campaign_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}