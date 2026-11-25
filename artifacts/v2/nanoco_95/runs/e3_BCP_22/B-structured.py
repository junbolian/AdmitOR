# IR: {"sets":{"V":"range(num_nodes)","E":[[0,1],[0,7],[1,4],[1,7],[4,5]]},"params":{"num_nodes":"params['num_nodes']","d[0,1]":"params['safety_buffer_0_1']","d[0,7]":"params['safety_buffer_0_7']","d[1,4]":"params['safety_buffer_1_4']","d[1,7]":"params['safety_buffer_1_7']","d[4,5]":"params['safety_buffer_4_5']"},"derived":{"D":"ceil(max(0,max(d[e] for e in E)))","U":"(num_nodes-1)*D","M[u,v]":"U+d[u,v]"},"variables":{"x[i]":"integer in [0,U]","peak":"integer in [0,U]","direction[u,v]":"binary"},"constraints":["x[i] <= peak for i in V","x[u]-x[v] >= d[u,v]-M[u,v]*(1-direction[u,v]) for (u,v) in E","x[v]-x[u] >= d[u,v]-M[u,v]*direction[u,v] for (u,v) in E"],"objective":"minimize peak"}

import math

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    buffers = {
        (0, 1): params["safety_buffer_0_1"],
        (0, 7): params["safety_buffer_0_7"],
        (1, 4): params["safety_buffer_1_4"],
        (1, 7): params["safety_buffer_1_7"],
        (4, 5): params["safety_buffer_4_5"],
    }

    max_separation = math.ceil(max(0, max(buffers.values())))
    slot_upper = (num_nodes - 1) * max_separation

    # Assigning x[i] = i * max_separation gives a feasible assignment
    # within this bound, so bounding the slots preserves an optimum.
    model = pyo.ConcreteModel()
    model.aircraft = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.conflict_pairs = pyo.Set(
        initialize=list(buffers),
        dimen=2,
        ordered=True,
    )
    model.safety_distance = pyo.Param(
        model.conflict_pairs,
        initialize=buffers,
        within=pyo.NonNegativeReals,
    )

    model.slot = pyo.Var(
        model.aircraft,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, slot_upper),
    )
    model.peak_slot = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, slot_upper),
    )
    model.direction = pyo.Var(model.conflict_pairs, domain=pyo.Binary)

    def peak_bound_rule(instance, aircraft):
        return instance.slot[aircraft] <= instance.peak_slot

    model.peak_bounds = pyo.Constraint(
        model.aircraft,
        rule=peak_bound_rule,
    )

    def forward_separation_rule(instance, u, v):
        distance = instance.safety_distance[u, v]
        big_m = slot_upper + distance
        return (
            instance.slot[u] - instance.slot[v]
            >= distance - big_m * (1 - instance.direction[u, v])
        )

    model.forward_separation = pyo.Constraint(
        model.conflict_pairs,
        rule=forward_separation_rule,
    )

    def reverse_separation_rule(instance, u, v):
        distance = instance.safety_distance[u, v]
        big_m = slot_upper + distance
        return (
            instance.slot[v] - instance.slot[u]
            >= distance - big_m * instance.direction[u, v]
        )

    model.reverse_separation = pyo.Constraint(
        model.conflict_pairs,
        rule=reverse_separation_rule,
    )

    model.objective = pyo.Objective(
        expr=model.peak_slot,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}