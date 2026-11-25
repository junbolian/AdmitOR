# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":[[0,1],[0,2],[1,3],[1,4],[1,5],[2,7],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6]]},"params":{"w[e]":"params['edge_weights'] in E order; finite, nonnegative","U":"(|V|-1)*max(ceil(w[e]) for e in E)"},"variables":{"track[v]":"integer, 0<=track[v]<=U","span":"integer, 0<=span<=U","direction[e]":"binary"},"constraints":["track[v]<=span for v in V","track[u]-track[v]>=w[u,v]-(U+w[u,v])*(1-direction[u,v]) for (u,v) in E","track[v]-track[u]>=w[u,v]-(U+w[u,v])*direction[u,v] for (u,v) in E"],"objective":"minimize span"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(8))
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

    weights = tuple(float(value) for value in params["edge_weights"])
    if len(weights) != len(edges):
        return {"objective": None, "status": "invalid_edge_weights"}
    if any(not math.isfinite(value) or value < 0 for value in weights):
        return {"objective": None, "status": "invalid_edge_weights"}

    # Equally spaced tracks with spacing max(ceil(w)) give a feasible
    # assignment within this bound, so imposing it preserves optimality.
    upper_bound = (len(vertices) - 1) * max(
        math.ceil(value) for value in weights
    )

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.separation = pyo.Param(
        model.edges,
        initialize=dict(zip(edges, weights)),
        within=pyo.NonNegativeReals,
    )
    model.track_limit = pyo.Param(
        initialize=upper_bound,
        within=pyo.NonNegativeIntegers,
    )

    model.track = pyo.Var(
        model.vertices,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.span = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.direction = pyo.Var(model.edges, domain=pyo.Binary)

    def span_rule(instance, vertex):
        return instance.track[vertex] <= instance.span

    model.span_constraints = pyo.Constraint(
        model.vertices, rule=span_rule
    )

    def forward_rule(instance, source, target):
        distance = instance.separation[source, target]
        big_m = instance.track_limit + distance
        return (
            instance.track[source] - instance.track[target]
            >= distance
            - big_m * (1 - instance.direction[source, target])
        )

    def reverse_rule(instance, source, target):
        distance = instance.separation[source, target]
        big_m = instance.track_limit + distance
        return (
            instance.track[target] - instance.track[source]
            >= distance - big_m * instance.direction[source, target]
        )

    model.forward_constraints = pyo.Constraint(
        model.edges, rule=forward_rule
    )
    model.reverse_constraints = pyo.Constraint(
        model.edges, rule=reverse_rule
    )
    model.objective = pyo.Objective(
        expr=model.span,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}