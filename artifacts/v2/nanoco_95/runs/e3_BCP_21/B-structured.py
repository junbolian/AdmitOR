# IR: {"sets":{"N":"0..7","E":[[0,1],[0,2],[1,3],[1,4],[1,5],[2,7],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6]]},"params":{"d[e]":"params['separation_weight'][e]","U":"(|N|-1)*ceil(max(0,max_e d[e]))","M[e]":"U+d[e]"},"variables":{"x[i]":"integer, 0<=x[i]<=U","z":"integer, 0<=z<=U","b[e]":"binary"},"constraints":["x[i]<=z for i in N","x[u]-x[v]>=d[e]-M[e]*(1-b[e]) for e=(u,v) in E","x[v]-x[u]>=d[e]-M[e]*b[e] for e=(u,v) in E"],"objective":"minimize z"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 1),
        (0, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (2, 7),
        (3, 4),
        (3, 5),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 6),
    )
    nets = tuple(range(8))

    supplied_weights = params["separation_weight"]
    if len(supplied_weights) != len(edges):
        raise ValueError("separation_weight must contain exactly 12 values.")

    weights = {
        edge_idx: float(supplied_weights[edge_idx])
        for edge_idx in range(len(edges))
    }
    if any(not math.isfinite(weight) for weight in weights.values()):
        raise ValueError("All separation weights must be finite.")

    # Equally spaced tracks establish a valid upper bound on the optimum.
    spacing = math.ceil(max(0, max(weights.values())))
    upper_bound = (len(nets) - 1) * spacing

    model = pyo.ConcreteModel()
    model.net_ids = pyo.Set(initialize=nets, ordered=True)
    model.edge_ids = pyo.Set(initialize=range(len(edges)), ordered=True)

    model.separation = pyo.Param(
        model.edge_ids, initialize=weights, within=pyo.Reals
    )
    model.span_bound = pyo.Param(
        initialize=upper_bound, within=pyo.NonNegativeIntegers
    )
    model.big_m = pyo.Expression(
        model.edge_ids,
        rule=lambda mdl, edge_idx: (
            mdl.span_bound + mdl.separation[edge_idx]
        ),
    )

    model.track = pyo.Var(
        model.net_ids,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.maximum_track = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.orientation = pyo.Var(model.edge_ids, domain=pyo.Binary)

    def span_rule(mdl, net_idx):
        return mdl.track[net_idx] <= mdl.maximum_track

    model.span_limits = pyo.Constraint(model.net_ids, rule=span_rule)

    def forward_rule(mdl, edge_idx):
        source, target = edges[edge_idx]
        return (
            mdl.track[source] - mdl.track[target]
            >= mdl.separation[edge_idx]
            - mdl.big_m[edge_idx] * (1 - mdl.orientation[edge_idx])
        )

    def reverse_rule(mdl, edge_idx):
        source, target = edges[edge_idx]
        return (
            mdl.track[target] - mdl.track[source]
            >= mdl.separation[edge_idx]
            - mdl.big_m[edge_idx] * mdl.orientation[edge_idx]
        )

    model.forward_separation = pyo.Constraint(
        model.edge_ids, rule=forward_rule
    )
    model.reverse_separation = pyo.Constraint(
        model.edge_ids, rule=reverse_rule
    )

    model.total_span = pyo.Objective(
        expr=model.maximum_track, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_span))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}