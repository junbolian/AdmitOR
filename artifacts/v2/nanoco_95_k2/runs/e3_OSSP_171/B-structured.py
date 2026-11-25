# IR: {"sets":{"J":["J0","J1","J2"],"M":["M0","M1","M2"],"O":"J x M","K":"unordered pairs of distinct operations sharing a lot or tool"},"params":{"p[j,t]":"params['p_'+j+'_'+t], nonnegative","H":"sum(p[j,t] for (j,t) in O)"},"variables":{"s[j,t]":"continuous >= 0","y[a,b]":"binary for (a,b) in K; 1 means a precedes b","C":"continuous >= 0"},"constraints":["s[j,t] + p[j,t] <= C for each (j,t) in O","s[a] + p[a] <= s[b] + H*(1-y[a,b]) for each (a,b) in K","s[b] + p[b] <= s[a] + H*y[a,b] for each (a,b) in K","C <= H"],"objective":"minimize C"}
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lots = ("J0", "J1", "J2")
    tools = ("M0", "M1", "M2")

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

    operations = [(lot, tool) for lot in lots for tool in tools]
    conflict_pairs = [
        (lot_a, tool_a, lot_b, tool_b)
        for (lot_a, tool_a), (lot_b, tool_b) in combinations(operations, 2)
        if lot_a == lot_b or tool_a == tool_b
    ]

    model = pyo.ConcreteModel()
    model.lots = pyo.Set(initialize=lots, ordered=True)
    model.tools = pyo.Set(initialize=tools, ordered=True)
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
    model.horizon = pyo.Expression(
        expr=sum(
            model.processing_time[lot, tool]
            for lot, tool in model.operations
        )
    )

    model.start_time = pyo.Var(
        model.operations, domain=pyo.NonNegativeReals
    )
    model.precedes = pyo.Var(model.conflict_pairs, domain=pyo.Binary)
    model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

    def completion_rule(block, lot, tool):
        return (
            block.start_time[lot, tool]
            + block.processing_time[lot, tool]
            <= block.makespan
        )

    model.completion_limit = pyo.Constraint(
        model.operations, rule=completion_rule
    )

    def forward_order_rule(block, lot_a, tool_a, lot_b, tool_b):
        return (
            block.start_time[lot_a, tool_a]
            + block.processing_time[lot_a, tool_a]
            <= block.start_time[lot_b, tool_b]
            + block.horizon
            * (1 - block.precedes[lot_a, tool_a, lot_b, tool_b])
        )

    model.forward_order = pyo.Constraint(
        model.conflict_pairs, rule=forward_order_rule
    )

    def reverse_order_rule(block, lot_a, tool_a, lot_b, tool_b):
        return (
            block.start_time[lot_b, tool_b]
            + block.processing_time[lot_b, tool_b]
            <= block.start_time[lot_a, tool_a]
            + block.horizon
            * block.precedes[lot_a, tool_a, lot_b, tool_b]
        )

    model.reverse_order = pyo.Constraint(
        model.conflict_pairs, rule=reverse_order_rule
    )
    model.horizon_limit = pyo.Constraint(
        expr=model.makespan <= model.horizon
    )

    model.total_cycle_time = pyo.Objective(
        expr=model.makespan, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}