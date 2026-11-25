# IR: {"sets":{"V":"range(num_nodes)","E":[[0,1],[0,7],[1,4],[1,7],[4,5]]},"params":{"num_nodes":"params['num_nodes']; frozen at 8","d[0,1]":"params['safety_buffer_0_1']","d[0,7]":"params['safety_buffer_0_7']","d[1,4]":"params['safety_buffer_1_4']","d[1,7]":"params['safety_buffer_1_7']","d[4,5]":"params['safety_buffer_4_5']"},"derived":{"U":"(num_nodes-1)*ceil(max(d[e] for e in E))","M[e]":"U+d[e]"},"variables":{"x[i]":"integer in [0,U]","t":"integer in [0,U]","y[e]":"binary"},"constraints":["x[i] <= t for i in V","x[u]-x[v] >= d[u,v]-M[u,v]*(1-y[u,v]) for (u,v) in E","x[v]-x[u] >= d[u,v]-M[u,v]*y[u,v] for (u,v) in E"],"objective":"minimize t"}

from math import ceil

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    if num_nodes != 8:
        raise ValueError("num_nodes must equal the frozen index-set size of 8.")

    buffer_values = {
        (0, 1): params["safety_buffer_0_1"],
        (0, 7): params["safety_buffer_0_7"],
        (1, 4): params["safety_buffer_1_4"],
        (1, 7): params["safety_buffer_1_7"],
        (4, 5): params["safety_buffer_4_5"],
    }

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, num_nodes - 1)
    model.conflict_pairs = pyo.Set(
        dimen=2, initialize=list(buffer_values)
    )
    model.safety_distance = pyo.Param(
        model.conflict_pairs,
        initialize=buffer_values,
        within=pyo.NonNegativeReals,
    )

    # Uniform spacing by the largest rounded-up buffer gives a feasible
    # assignment within this bound, so the bound preserves an optimum.
    upper_bound = (num_nodes - 1) * ceil(max(buffer_values.values()))

    model.gate_slot = pyo.Var(
        model.aircraft,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.highest_slot = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.pair_order = pyo.Var(
        model.conflict_pairs,
        domain=pyo.Binary,
    )

    def highest_slot_rule(block, aircraft_id):
        return block.gate_slot[aircraft_id] <= block.highest_slot

    model.slot_ceiling = pyo.Constraint(
        model.aircraft,
        rule=highest_slot_rule,
    )

    def forward_separation_rule(block, node_u, node_v):
        distance = block.safety_distance[node_u, node_v]
        big_m = upper_bound + distance
        return (
            block.gate_slot[node_u] - block.gate_slot[node_v]
            >= distance - big_m * (1 - block.pair_order[node_u, node_v])
        )

    model.forward_separation = pyo.Constraint(
        model.conflict_pairs,
        rule=forward_separation_rule,
    )

    def reverse_separation_rule(block, node_u, node_v):
        distance = block.safety_distance[node_u, node_v]
        big_m = upper_bound + distance
        return (
            block.gate_slot[node_v] - block.gate_slot[node_u]
            >= distance - big_m * block.pair_order[node_u, node_v]
        )

    model.reverse_separation = pyo.Constraint(
        model.conflict_pairs,
        rule=reverse_separation_rule,
    )

    model.minimize_highest_slot = pyo.Objective(
        expr=model.highest_slot,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.minimize_highest_slot))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}