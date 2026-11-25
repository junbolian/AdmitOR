# IR: {"sets":{"N":"0,...,num_nodes-1 (num_nodes frozen at 8)","E":[[0,1],[0,7],[1,4],[1,7],[4,5]]},"params":{"num_nodes":"params['num_nodes']","d[0,1]":"params['safety_buffer_0_1']","d[0,7]":"params['safety_buffer_0_7']","d[1,4]":"params['safety_buffer_1_4']","d[1,7]":"params['safety_buffer_1_7']","d[4,5]":"params['safety_buffer_4_5']"},"derived":{"U":"(num_nodes-1)*max(ceil(d[e]) for e in E)","M[e]":"U+d[e]"},"variables":{"x[i]":"integer in [0,U], i in N","z":"integer in [0,U]","b[u,v]":"binary, (u,v) in E"},"constraints":["x[i] <= z for i in N","x[u]-x[v] >= d[u,v]-M[u,v]*(1-b[u,v]) for (u,v) in E","x[v]-x[u] >= d[u,v]-M[u,v]*b[u,v] for (u,v) in E"],"objective":"minimize z"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    if num_nodes != 8:
        raise ValueError("num_nodes must equal 8 for the frozen index structure.")
    num_nodes = int(num_nodes)

    safety_distances = {
        (0, 1): params["safety_buffer_0_1"],
        (0, 7): params["safety_buffer_0_7"],
        (1, 4): params["safety_buffer_1_4"],
        (1, 7): params["safety_buffer_1_7"],
        (4, 5): params["safety_buffer_4_5"],
    }

    for distance in safety_distances.values():
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Safety buffers must be finite and nonnegative.")

    # Assigning aircraft i to i*max_distance proves this upper bound
    # admits a feasible assignment and preserves the optimal objective.
    max_distance = max(
        math.ceil(distance) for distance in safety_distances.values()
    )
    upper_bound = (num_nodes - 1) * max_distance

    model = pyo.ConcreteModel()
    model.aircraft = pyo.RangeSet(0, num_nodes - 1)
    model.conflict_pairs = pyo.Set(
        dimen=2, initialize=list(safety_distances)
    )
    model.safety_distance = pyo.Param(
        model.conflict_pairs,
        initialize=safety_distances,
        within=pyo.NonNegativeReals,
    )

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

    def slot_limit_rule(instance, aircraft):
        return instance.gate_slot[aircraft] <= instance.highest_slot

    model.slot_limit = pyo.Constraint(
        model.aircraft, rule=slot_limit_rule
    )

    def forward_separation_rule(instance, node_u, node_v):
        distance = instance.safety_distance[node_u, node_v]
        big_m = upper_bound + distance
        return (
            instance.gate_slot[node_u] - instance.gate_slot[node_v]
            >= distance - big_m * (1 - instance.pair_order[node_u, node_v])
        )

    model.forward_separation = pyo.Constraint(
        model.conflict_pairs, rule=forward_separation_rule
    )

    def reverse_separation_rule(instance, node_u, node_v):
        distance = instance.safety_distance[node_u, node_v]
        big_m = upper_bound + distance
        return (
            instance.gate_slot[node_v] - instance.gate_slot[node_u]
            >= distance - big_m * instance.pair_order[node_u, node_v]
        )

    model.reverse_separation = pyo.Constraint(
        model.conflict_pairs, rule=reverse_separation_rule
    )

    model.objective = pyo.Objective(
        expr=model.highest_slot,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when it cannot load a solution.
        # Other runtime errors remain visible to the calling harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}