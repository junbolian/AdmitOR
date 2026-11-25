# IR: {"sets":{"lots":[0,1,2],"tools":[0,1,2],"route":[1,0,2],"pairs":[[0,1],[0,2],[1,2]],"steps":[0,1]},"params":{"p[l,t]":"params['processing_times'][l][t]","H":"sum(p[l,t] for all lots l and tools t)"},"variables":{"start[l,t]":"continuous >= 0","before[a,b,t]":"binary for (a,b) in pairs","makespan":"continuous in [0,H]"},"constraints":["start[l,route[k+1]] >= start[l,route[k]] + p[l,route[k]] for every lot l and step k","start[a,t] + p[a,t] <= start[b,t] + H*(1-before[a,b,t]) for every pair (a,b) and tool t","start[b,t] + p[b,t] <= start[a,t] + H*before[a,b,t] for every pair (a,b) and tool t","makespan >= start[l,t] + p[l,t] for every lot l and tool t"],"objective":"minimize makespan"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = params["processing_times"]
    durations = {
        (lot, tool): float(processing_times[lot][tool])
        for lot in range(3)
        for tool in range(3)
    }

    if any(
        not math.isfinite(duration) or duration < 0
        for duration in durations.values()
    ):
        return {"objective": None, "status": "invalid_processing_times"}

    horizon = sum(durations.values())
    route = (1, 0, 2)

    model = pyo.ConcreteModel()
    model.lots = pyo.RangeSet(0, 2)
    model.tools = pyo.RangeSet(0, 2)
    model.steps = pyo.RangeSet(0, 1)
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 2)],
    )

    model.duration = pyo.Param(
        model.lots,
        model.tools,
        initialize=durations,
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(
        model.lots,
        model.tools,
        domain=pyo.NonNegativeReals,
    )
    model.before = pyo.Var(
        model.pairs,
        model.tools,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def precedence_rule(instance, lot, step):
        current_tool = route[step]
        next_tool = route[step + 1]
        return (
            instance.start[lot, next_tool]
            >= instance.start[lot, current_tool]
            + instance.duration[lot, current_tool]
        )

    model.precedence = pyo.Constraint(
        model.lots,
        model.steps,
        rule=precedence_rule,
    )

    def forward_exclusion_rule(instance, first_lot, second_lot, tool):
        return (
            instance.start[first_lot, tool]
            + instance.duration[first_lot, tool]
            <= instance.start[second_lot, tool]
            + instance.horizon
            * (1 - instance.before[first_lot, second_lot, tool])
        )

    model.forward_exclusion = pyo.Constraint(
        model.pairs,
        model.tools,
        rule=forward_exclusion_rule,
    )

    def reverse_exclusion_rule(instance, first_lot, second_lot, tool):
        return (
            instance.start[second_lot, tool]
            + instance.duration[second_lot, tool]
            <= instance.start[first_lot, tool]
            + instance.horizon
            * instance.before[first_lot, second_lot, tool]
        )

    model.reverse_exclusion = pyo.Constraint(
        model.pairs,
        model.tools,
        rule=reverse_exclusion_rule,
    )

    def completion_rule(instance, lot, tool):
        return (
            instance.makespan
            >= instance.start[lot, tool] + instance.duration[lot, tool]
        )

    model.completion = pyo.Constraint(
        model.lots,
        model.tools,
        rule=completion_rule,
    )

    model.total_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}