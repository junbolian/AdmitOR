# IR: {"sets":{"B":[0,1,2,3],"K":[0,1,2,3],"S":[0,1,2]},"params":{"processing_times":"params['processing_times'][b][s]"},"variables":{"assigned[b,k]":"binary; batch b occupies position k on every stage","completion[k,s]":"nonnegative continuous; completion time at position k, stage s"},"expressions":{"duration[k,s]":"sum(processing_times[b][s]*assigned[b,k] for b in B)"},"constraints":["sum(assigned[b,k] for k in K)=1 for each b in B","sum(assigned[b,k] for b in B)=1 for each k in K","completion[k,s]>=duration[k,s] for each k in K,s in S","completion[0,0]=duration[0,0]","completion[k,s]>=completion[k,s-1]+duration[k,s] for each k in K,s in S with s>0","completion[k,s]>=completion[k-1,s]+duration[k,s] for each k in K with k>0,s in S"],"objective":"minimize completion[3,2]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]

    model = pyo.ConcreteModel()
    model.B = pyo.RangeSet(0, 3)
    model.K = pyo.RangeSet(0, 3)
    model.S = pyo.RangeSet(0, 2)

    model.processing_duration = pyo.Param(
        model.B,
        model.S,
        initialize=lambda mdl, batch, stage: processing_times[batch][stage],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(model.B, model.K, domain=pyo.Binary)
    model.completion = pyo.Var(
        model.K, model.S, domain=pyo.NonNegativeReals
    )

    model.duration = pyo.Expression(
        model.K,
        model.S,
        rule=lambda mdl, position, stage: sum(
            mdl.processing_duration[batch, stage]
            * mdl.assigned[batch, position]
            for batch in mdl.B
        ),
    )

    model.batch_assignment = pyo.Constraint(
        model.B,
        rule=lambda mdl, batch: sum(
            mdl.assigned[batch, position] for position in mdl.K
        ) == 1,
    )

    model.position_assignment = pyo.Constraint(
        model.K,
        rule=lambda mdl, position: sum(
            mdl.assigned[batch, position] for batch in mdl.B
        ) == 1,
    )

    model.nonnegative_start = pyo.Constraint(
        model.K,
        model.S,
        rule=lambda mdl, position, stage: (
            mdl.completion[position, stage] >= mdl.duration[position, stage]
        ),
    )

    model.first_entry = pyo.Constraint(
        expr=model.completion[0, 0] == model.duration[0, 0]
    )

    def stage_precedence_rule(mdl, position, stage):
        if stage == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, stage]
            >= mdl.completion[position, stage - 1]
            + mdl.duration[position, stage]
        )

    model.stage_precedence = pyo.Constraint(
        model.K, model.S, rule=stage_precedence_rule
    )

    def machine_capacity_rule(mdl, position, stage):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, stage]
            >= mdl.completion[position - 1, stage]
            + mdl.duration[position, stage]
        )

    model.machine_capacity = pyo.Constraint(
        model.K, model.S, rule=machine_capacity_rule
    )

    model.makespan = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}