# IR: {"sets":{"B":[0,1,2],"S":[0,1,2],"P":[[0,1],[0,2],[1,2]]},"params":{"p[b,s]":"params['processing_time'][b][s], nonnegative","H":"sum(p[b,s] for b in B for s in S)"},"variables":{"start[b,s]":"continuous, 0 <= start <= H","before[i,j,s]":"binary for (i,j) in P, s in S","makespan":"continuous, 0 <= makespan <= H"},"expressions":{"completion[b,s]":"start[b,s] + p[b,s]"},"constraints":["completion[b,s] <= H for all b,s","start[b,1] == completion[b,0] for all b (immediate transfer)","start[b,2] >= completion[b,1] for all b","start[j,s] >= completion[i,s] - H*(1-before[i,j,s]) for all (i,j),s","start[i,s] >= completion[j,s] - H*before[i,j,s] for all (i,j),s","makespan >= completion[b,2] for all b"],"objective":"minimize makespan"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        (batch, station): float(params["processing_time"][batch][station])
        for batch in range(3)
        for station in range(3)
    }

    model = pyo.ConcreteModel()
    model.batches = pyo.Set(initialize=range(3), ordered=True)
    model.stations = pyo.Set(initialize=range(3), ordered=True)
    model.batch_pairs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 2)],
    )
    model.duration = pyo.Param(
        model.batches,
        model.stations,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    # A fully serial schedule satisfies the immediate-transfer requirement
    # and finishes within the sum of all processing times.
    horizon = float(sum(pyo.value(model.duration[key]) for key in model.duration))

    model.start = pyo.Var(
        model.batches,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.batch_pairs,
        model.stations,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    model.completion = pyo.Expression(
        model.batches,
        model.stations,
        rule=lambda mdl, batch, station: (
            mdl.start[batch, station] + mdl.duration[batch, station]
        ),
    )
    model.finish_within_horizon = pyo.Constraint(
        model.batches,
        model.stations,
        rule=lambda mdl, batch, station: (
            mdl.completion[batch, station] <= horizon
        ),
    )
    model.immediate_transfer = pyo.Constraint(
        model.batches,
        rule=lambda mdl, batch: (
            mdl.start[batch, 1] == mdl.completion[batch, 0]
        ),
    )
    model.final_stage_precedence = pyo.Constraint(
        model.batches,
        rule=lambda mdl, batch: (
            mdl.start[batch, 2] >= mdl.completion[batch, 1]
        ),
    )
    model.first_before_second = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=lambda mdl, first, second, station: (
            mdl.start[second, station]
            >= mdl.completion[first, station]
            - horizon * (1 - mdl.before[first, second, station])
        ),
    )
    model.second_before_first = pyo.Constraint(
        model.batch_pairs,
        model.stations,
        rule=lambda mdl, first, second, station: (
            mdl.start[first, station]
            >= mdl.completion[second, station]
            - horizon * mdl.before[first, second, station]
        ),
    )
    model.makespan_requirement = pyo.Constraint(
        model.batches,
        rule=lambda mdl, batch: (
            mdl.makespan >= mdl.completion[batch, 2]
        ),
    )
    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}