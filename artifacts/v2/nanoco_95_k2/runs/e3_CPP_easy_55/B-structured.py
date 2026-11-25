# IR: {"sets":{"N":"nodes 0..6; depot 0","K":"0..num_graph_edges-1","R":"0..num_required_edges-1","E":"[(0,1),(0,2),(1,3),(2,6),(3,4),(3,5),(3,6),(5,6)]","S":"(k,u,v) and (k,v,u) for required edge k=(u,v)","A":"all ordered node pairs (u,v), u!=v","C":"all nonempty subsets of N excluding depot 0"},"params":{"node_coords":"node coordinates; descriptive only","num_graph_edges":"frozen graph edge count, equal to len(E)","num_required_edges":"frozen required edge count, equal to len(E)","service_costs":"service cost indexed by R","travel_cost_matrix":"directed deadhead cost indexed by N x N"},"variables":{"service[k,u,v]":"binary; service edge k in direction u->v","deadhead[u,v]":"nonnegative integer; deadhead traversal count"},"constraints":["For each required edge k=(u,v): service[k,u,v]+service[k,v,u]=1.","For every node: total incoming service and deadhead traversals equals total outgoing traversals.","For every U in C: at least one service or deadhead traversal leaves U."],"objective":"Minimize sum(service_costs[k]*service[k,u,v] over S)+sum(travel_cost_matrix[u][v]*deadhead[u,v] over A)."}
from itertools import combinations
from operator import index

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_coords = params["node_coords"]
    num_graph_edges = index(params["num_graph_edges"])
    num_required_edges = index(params["num_required_edges"])
    service_costs = params["service_costs"]
    travel_cost_matrix = params["travel_cost_matrix"]

    nodes = tuple(range(7))
    graph_edges = (
        (0, 1),
        (0, 2),
        (1, 3),
        (2, 6),
        (3, 4),
        (3, 5),
        (3, 6),
        (5, 6),
    )

    if (
        num_graph_edges != len(graph_edges)
        or num_required_edges != len(graph_edges)
    ):
        return {"objective": None, "status": "invalid_edge_counts"}

    required_edges = graph_edges
    graph_ids = tuple(range(num_graph_edges))
    required_ids = tuple(range(num_required_edges))

    service_arcs = tuple(
        arc
        for edge_id in required_ids
        for u, v in (required_edges[edge_id],)
        for arc in ((edge_id, u, v), (edge_id, v, u))
    )
    deadhead_arcs = tuple(
        (u, v) for u in nodes for v in nodes if u != v
    )

    nondepot_nodes = tuple(node for node in nodes if node != 0)
    connectivity_subsets = tuple(
        frozenset(subset)
        for subset_size in range(1, len(nondepot_nodes) + 1)
        for subset in combinations(nondepot_nodes, subset_size)
    )

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)
    model.graph_ids = pyo.Set(initialize=graph_ids, ordered=True)
    model.required_ids = pyo.Set(initialize=required_ids, ordered=True)
    model.graph_edges = pyo.Set(
        dimen=2, initialize=graph_edges, ordered=True
    )
    model.service_arcs = pyo.Set(
        dimen=3, initialize=service_arcs, ordered=True
    )
    model.deadhead_arcs = pyo.Set(
        dimen=2, initialize=deadhead_arcs, ordered=True
    )
    model.cut_ids = pyo.Set(
        initialize=range(len(connectivity_subsets)), ordered=True
    )

    model.graph_edge_count = pyo.Param(
        initialize=num_graph_edges, within=pyo.NonNegativeIntegers
    )
    model.required_edge_count = pyo.Param(
        initialize=num_required_edges, within=pyo.NonNegativeIntegers
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize={
            (node, axis): node_coords[node][axis]
            for node in nodes
            for axis in (0, 1)
        },
        within=pyo.Reals,
    )
    model.service_cost = pyo.Param(
        model.required_ids,
        initialize={
            edge_id: service_costs[edge_id] for edge_id in required_ids
        },
        within=pyo.NonNegativeReals,
    )
    model.travel_cost = pyo.Param(
        model.nodes,
        model.nodes,
        initialize={
            (u, v): travel_cost_matrix[u][v]
            for u in nodes
            for v in nodes
        },
        within=pyo.NonNegativeReals,
    )

    model.service = pyo.Var(model.service_arcs, domain=pyo.Binary)
    model.deadhead = pyo.Var(
        model.deadhead_arcs, domain=pyo.NonNegativeIntegers
    )

    # One traversal supplies each required service. Any additional traversal
    # is represented as deadheading, including travel over a required edge.
    def service_rule(instance, edge_id):
        u, v = required_edges[edge_id]
        return (
            instance.service[edge_id, u, v]
            + instance.service[edge_id, v, u]
            == 1
        )

    model.required_service = pyo.Constraint(
        model.required_ids, rule=service_rule
    )

    def balance_rule(instance, node):
        incoming = sum(
            instance.service[edge_id, u, v]
            for edge_id, u, v in service_arcs
            if v == node
        ) + sum(
            instance.deadhead[u, v]
            for u, v in deadhead_arcs
            if v == node
        )
        outgoing = sum(
            instance.service[edge_id, u, v]
            for edge_id, u, v in service_arcs
            if u == node
        ) + sum(
            instance.deadhead[u, v]
            for u, v in deadhead_arcs
            if u == node
        )
        return incoming == outgoing

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def connectivity_rule(instance, cut_id):
        subset = connectivity_subsets[cut_id]
        return (
            sum(
                instance.service[edge_id, u, v]
                for edge_id, u, v in service_arcs
                if u in subset and v not in subset
            )
            + sum(
                instance.deadhead[u, v]
                for u, v in deadhead_arcs
                if u in subset and v not in subset
            )
            >= 1
        )

    model.depot_connectivity = pyo.Constraint(
        model.cut_ids, rule=connectivity_rule
    )

    # Connectivity and balanced integral traversals give a single Euler
    # tour that can start and end at the garage.
    model.total_distance = pyo.Objective(
        expr=sum(
            model.service_cost[edge_id] * model.service[edge_id, u, v]
            for edge_id, u, v in service_arcs
        )
        + sum(
            model.travel_cost[u, v] * model.deadhead[u, v]
            for u, v in deadhead_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}