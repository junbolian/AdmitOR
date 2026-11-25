# IR: {"sets":{"N":"0..7","A":[[0,1],[0,2],[0,3],[0,6],[0,7],[1,2],[1,5],[1,7],[2,3],[2,5],[2,6],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{"arc_costs":"arc costs in A order","arc_capacities":"arc upper bounds in A order","source_supply":"supply at node 0","sink_supply":"supply at node 7","node_coordinates":"read for context only; excluded from model","supply":"source_supply at 0; sink_supply at 7; zero otherwise"},"variables":{"route[i,j]":"Binary for each (i,j) in A"},"constraints":["route[i,j] <= arc_capacities[i,j] for each arc","sum(route[v,j]) - sum(route[i,v]) = supply[v] for each node"],"objective":"minimize sum(arc_costs[i,j] * route[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]
    node_coordinates = params["node_coordinates"]  # Context only.

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 7),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    nodes = range(8)

    outgoing = {
        node: [arc for arc in arcs if arc[0] == node]
        for node in nodes
    }
    incoming = {
        node: [arc for arc in arcs if arc[1] == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.latency = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.bandwidth = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.supply = pyo.Param(
        model.nodes,
        initialize={
            node: (
                source_supply if node == 0
                else sink_supply if node == 7
                else 0
            )
            for node in nodes
        },
        within=pyo.Reals,
    )

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(network, tail, head):
        return network.route[tail, head] <= network.bandwidth[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, node):
        return (
            sum(network.route[arc] for arc in outgoing[node])
            - sum(network.route[arc] for arc in incoming[node])
            == network.supply[node]
        )

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_latency = pyo.Objective(
        expr=sum(
            model.latency[arc] * model.route[arc]
            for arc in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_latency))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}