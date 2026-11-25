# IR: {"sets":{"nodes":"0..8","arcs":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"capacity":"params['capacity']: 14 nonnegative capacities in arc order","cost":"params['cost']: 14 transportation costs in arc order; unused in minimum-cut objective"},"variables":{"source_side[node]":"binary; 1 iff node belongs to source side","severed[u,v]":"binary; 1 iff arc crosses from source side to sink side"},"constraints":["source_side[0] = 1","source_side[8] = 0","severed[u,v] >= source_side[u] - source_side[v] for every arc","severed[u,v] <= source_side[u] for every arc","severed[u,v] <= 1 - source_side[v] for every arc"],"objective":"minimize sum(capacity[u,v] * severed[u,v] for every arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    capacities = params["capacity"]
    costs = params["cost"]

    if len(capacities) != len(arcs) or len(costs) != len(arcs):
        raise ValueError("capacity and cost must each contain 14 entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 8)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )

    model.source_side = pyo.Var(model.nodes, domain=pyo.Binary)
    model.severed = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_side[0].fix(1)
    model.source_side[8].fix(0)

    def crossing_lower_rule(network, tail, head):
        return (
            network.severed[tail, head]
            >= network.source_side[tail] - network.source_side[head]
        )

    def crossing_tail_rule(network, tail, head):
        return network.severed[tail, head] <= network.source_side[tail]

    def crossing_head_rule(network, tail, head):
        return network.severed[tail, head] <= 1 - network.source_side[head]

    model.crossing_lower = pyo.Constraint(
        model.arcs, rule=crossing_lower_rule
    )
    model.crossing_tail = pyo.Constraint(
        model.arcs, rule=crossing_tail_rule
    )
    model.crossing_head = pyo.Constraint(
        model.arcs, rule=crossing_head_rule
    )

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.capacity[tail, head] * model.severed[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}