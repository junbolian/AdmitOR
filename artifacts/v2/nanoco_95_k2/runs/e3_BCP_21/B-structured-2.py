# {
#   "sets": {"nets": [0,1,2,3,4,5,6,7], "edges": [[0,1],[0,2],[1,3],[1,4],[1,5],[2,7],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6]]},
#   "params": {"edge_weights": "12 finite nonnegative distances, read from params"},
#   "derived": {"d[e]": "ceil(edge_weights[e])", "U": "(len(nets)-1)*max(d)", "M[e]": "U+d[e]"},
#   "variables": {"track[v]": "integer in [0,U]", "direction[e]": "binary", "span": "integer in [0,U]"},
#   "constraints": [
#     "For every net v: track[v] <= span",
#     "For every edge e=(u,v): track[u]-track[v] >= d[e]-M[e]*(1-direction[e])",
#     "For every edge e=(u,v): track[v]-track[u] >= d[e]-M[e]*direction[e]"
#   ],
#   "objective": "minimize span"
# }

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nets = tuple(range(8))
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

    edge_weights = tuple(float(value) for value in params["edge_weights"])
    if len(edge_weights) != len(edges):
        return {"objective": None, "status": "invalid_weights"}
    if any(not math.isfinite(value) or value < 0 for value in edge_weights):
        return {"objective": None, "status": "invalid_weights"}

    distances = tuple(math.ceil(value) for value in edge_weights)

    # Assigning successive nets multiples of max(distances) is feasible.
    # Thus this upper bound preserves at least one optimal solution.
    upper_bound = (len(nets) - 1) * max(distances)

    model = pyo.ConcreteModel()
    model.nets = pyo.Set(initialize=nets, ordered=True)
    model.edge_ids = pyo.RangeSet(0, len(edges) - 1)

    model.separation = pyo.Param(
        model.edge_ids,
        initialize={edge_id: distances[edge_id] for edge_id in range(len(edges))},
        within=pyo.NonNegativeIntegers,
    )
    model.big_m = pyo.Param(
        model.edge_ids,
        initialize={
            edge_id: upper_bound + distances[edge_id]
            for edge_id in range(len(edges))
        },
        within=pyo.NonNegativeIntegers,
    )

    model.track = pyo.Var(
        model.nets,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )
    model.direction = pyo.Var(model.edge_ids, domain=pyo.Binary)
    model.span = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, upper_bound),
    )

    def span_rule(instance, net):
        return instance.track[net] <= instance.span

    model.span_limits = pyo.Constraint(model.nets, rule=span_rule)

    def forward_rule(instance, edge_id):
        net_u, net_v = edges[edge_id]
        return (
            instance.track[net_u] - instance.track[net_v]
            >= instance.separation[edge_id]
            - instance.big_m[edge_id] * (1 - instance.direction[edge_id])
        )

    model.forward_separation = pyo.Constraint(
        model.edge_ids, rule=forward_rule
    )

    def reverse_rule(instance, edge_id):
        net_u, net_v = edges[edge_id]
        return (
            instance.track[net_v] - instance.track[net_u]
            >= instance.separation[edge_id]
            - instance.big_m[edge_id] * instance.direction[edge_id]
        )

    model.reverse_separation = pyo.Constraint(
        model.edge_ids, rule=reverse_rule
    )

    model.total_span = pyo.Objective(expr=model.span, sense=pyo.minimize)

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_span))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}