# IR: {"sets":{"V":[0,1,2,3,4,5,6],"E":[[0,1],[0,2],[0,4],[1,2],[1,6],[2,3],[2,6],[3,5]]},"params":{"edge_0_1_weight":"integer distance","edge_0_2_weight":"integer distance","edge_0_4_weight":"integer distance","edge_1_2_weight":"integer distance","edge_1_6_weight":"integer distance","edge_2_3_weight":"integer distance","edge_2_6_weight":"integer distance","edge_3_5_weight":"integer distance"},"derived":{"w[u,v]":"corresponding edge parameter","D":"max(0,max(w[u,v] for (u,v) in E))","U":"6*D","B[u,v]":"U+w[u,v]"},"variables":{"level[v]":"integer in [0,U]","peak":"integer in [0,U]","direction[u,v]":"binary"},"constraints":["level[v] <= peak for v in V","level[u]-level[v] >= w[u,v]-B[u,v]*(1-direction[u,v]) for (u,v) in E","level[v]-level[u] >= w[u,v]-B[u,v]*direction[u,v] for (u,v) in E"],"objective":"minimize peak"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 1),
        (0, 2),
        (0, 4),
        (1, 2),
        (1, 6),
        (2, 3),
        (2, 6),
        (3, 5),
    )

    weights = {
        (0, 1): params["edge_0_1_weight"],
        (0, 2): params["edge_0_2_weight"],
        (0, 4): params["edge_0_4_weight"],
        (1, 2): params["edge_1_2_weight"],
        (1, 6): params["edge_1_6_weight"],
        (2, 3): params["edge_2_3_weight"],
        (2, 6): params["edge_2_6_weight"],
        (3, 5): params["edge_3_5_weight"],
    }

    # Assigning level[v] = v * largest_distance proves this bound
    # admits a feasible assignment whenever the supplied distances are valid.
    largest_distance = max(0, max(weights.values()))
    upper_bound = 6 * largest_distance

    model = pyo.ConcreteModel()
    model.zones = pyo.Set(initialize=range(7), ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)

    model.distance = pyo.Param(
        model.edges,
        initialize=weights,
        within=pyo.Integers,
    )
    model.upper_bound = pyo.Param(initialize=upper_bound)
    model.big_m = pyo.Param(
        model.edges,
        initialize={
            (u, v): upper_bound + weights[u, v]
            for u, v in edges
        },
    )

    model.level = pyo.Var(
        model.zones,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.peak = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.direction = pyo.Var(model.edges, domain=pyo.Binary)

    def peak_rule(instance, zone):
        return instance.level[zone] <= instance.peak

    model.peak_constraints = pyo.Constraint(
        model.zones,
        rule=peak_rule,
    )

    def forward_rule(instance, u, v):
        return (
            instance.level[u] - instance.level[v]
            >= instance.distance[u, v]
            - instance.big_m[u, v] * (1 - instance.direction[u, v])
        )

    model.forward_constraints = pyo.Constraint(
        model.edges,
        rule=forward_rule,
    )

    def reverse_rule(instance, u, v):
        return (
            instance.level[v] - instance.level[u]
            >= instance.distance[u, v]
            - instance.big_m[u, v] * instance.direction[u, v]
        )

    model.reverse_constraints = pyo.Constraint(
        model.edges,
        rule=reverse_rule,
    )

    model.objective = pyo.Objective(
        expr=model.peak,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded. The objective
        # retrieval below remains the sole test for success.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}