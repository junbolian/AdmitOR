# IR: {"sets":{"J":["J0","J1","J2"],"T":["M0","M1","M2"],"O":"J x T","K":"unordered pairs (a,b) of distinct operations sharing a lot or tool"},"params":{"p_J0_M0":"nonnegative processing time","p_J0_M1":"nonnegative processing time","p_J0_M2":"nonnegative processing time","p_J1_M0":"nonnegative processing time","p_J1_M1":"nonnegative processing time","p_J1_M2":"nonnegative processing time","p_J2_M0":"nonnegative processing time","p_J2_M1":"nonnegative processing time","p_J2_M2":"nonnegative processing time"},"derived":{"p[j,t]":"corresponding input processing time","H":"sum(p[j,t] for (j,t) in O)"},"variables":{"start[o]":"continuous in [0,H] for o in O","before[a,b]":"binary for (a,b) in K","makespan":"continuous in [0,H]"},"constraints":["start[o]+p[o] <= makespan for o in O","start[a]+p[a] <= start[b]+H*(1-before[a,b]) for (a,b) in K","start[b]+p[b] <= start[a]+H*before[a,b] for (a,b) in K"],"objective":"minimize makespan"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        ("J0", "M0"): params["p_J0_M0"],
        ("J0", "M1"): params["p_J0_M1"],
        ("J0", "M2"): params["p_J0_M2"],
        ("J1", "M0"): params["p_J1_M0"],
        ("J1", "M1"): params["p_J1_M1"],
        ("J1", "M2"): params["p_J1_M2"],
        ("J2", "M0"): params["p_J2_M0"],
        ("J2", "M1"): params["p_J2_M1"],
        ("J2", "M2"): params["p_J2_M2"],
    }

    model = pyo.ConcreteModel()
    model.lots = pyo.Set(initialize=["J0", "J1", "J2"], ordered=True)
    model.tools = pyo.Set(initialize=["M0", "M1", "M2"], ordered=True)

    operations = [
        (lot, tool) for lot in model.lots for tool in model.tools
    ]
    conflict_pairs = [
        (first[0], first[1], second[0], second[1])
        for first, second in combinations(operations, 2)
        if first[0] == second[0] or first[1] == second[1]
    ]

    model.operations = pyo.Set(
        dimen=2, initialize=operations, ordered=True
    )
    model.conflict_pairs = pyo.Set(
        dimen=4, initialize=conflict_pairs, ordered=True
    )
    model.processing_time = pyo.Param(
        model.operations,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    horizon = float(
        sum(
            pyo.value(model.processing_time[lot, tool])
            for lot, tool in operations
        )
    )

    model.start = pyo.Var(
        model.operations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.conflict_pairs,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def completion_rule(instance, lot, tool):
        return (
            instance.start[lot, tool]
            + instance.processing_time[lot, tool]
            <= instance.makespan
        )

    model.completion_limits = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    def forward_rule(instance, lot_a, tool_a, lot_b, tool_b):
        return (
            instance.start[lot_a, tool_a]
            + instance.processing_time[lot_a, tool_a]
            <= instance.start[lot_b, tool_b]
            + horizon
            * (1 - instance.before[lot_a, tool_a, lot_b, tool_b])
        )

    model.forward_nonoverlap = pyo.Constraint(
        model.conflict_pairs, rule=forward_rule
    )

    def reverse_rule(instance, lot_a, tool_a, lot_b, tool_b):
        return (
            instance.start[lot_b, tool_b]
            + instance.processing_time[lot_b, tool_b]
            <= instance.start[lot_a, tool_a]
            + horizon * instance.before[lot_a, tool_a, lot_b, tool_b]
        )

    model.reverse_nonoverlap = pyo.Constraint(
        model.conflict_pairs, rule=reverse_rule
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}