# IR: {"sets":{"V":"{0,...,11}","E":[[3,7],[1,6],[0,8],[1,9],[2,8],[4,5],[5,9],[4,11],[9,10],[0,10],[2,7],[1,5],[1,11],[4,7],[3,8],[5,11],[8,10],[0,9],[0,6],[2,3],[6,9]],"A":"Both orientations of every edge in E"},"params":{"edge_weights":"Real-valued latency for each edge, read from params in listed order; does not affect the leaf-count objective"},"variables":{"x[e]":"Binary: select undirected edge e","leaf[v]":"Binary: node v has degree exactly one","flow[i,j]":"Nonnegative continuous flow on arc (i,j)"},"expressions":{"degree[v]":"sum(x[e] for e incident to v)"},"constraints":["sum(x[e] for e in E) = |V|-1","flow[i,j] <= (|V|-1)*x[undirected_edge(i,j)] for every arc","outflow[v]-inflow[v] = |V|-1 if v=0, otherwise -1","degree[v] >= 2-leaf[v] for every node","degree[v] <= 1+(|V|-2)*(1-leaf[v]) for every node"],"objective":"Maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (3, 7), (1, 6), (0, 8), (1, 9), (2, 8),
        (4, 5), (5, 9), (4, 11), (9, 10), (0, 10),
        (2, 7), (1, 5), (1, 11), (4, 7), (3, 8),
        (5, 11), (8, 10), (0, 9), (0, 6), (2, 3),
        (6, 9),
    )
    nodes = tuple(range(12))
    node_count = len(nodes)
    weights = tuple(params["edge_weights"])
    if len(weights) != len(edges):
        raise ValueError("edge_weights must contain exactly 21 values.")

    arcs = tuple(
        arc
        for first, second in edges
        for arc in ((first, second), (second, first))
    )
    edge_for_arc = {
        arc: (first, second)
        for first, second in edges
        for arc in ((first, second), (second, first))
    }
    incident_edges = {
        vertex: tuple(edge for edge in edges if vertex in edge)
        for vertex in nodes
    }
    outgoing_arcs = {
        vertex: tuple(arc for arc in arcs if arc[0] == vertex)
        for vertex in nodes
    }
    incoming_arcs = {
        vertex: tuple(arc for arc in arcs if arc[1] == vertex)
        for vertex in nodes
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.edge_weights = pyo.Param(
        model.edges,
        initialize=dict(zip(edges, weights)),
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)
    model.leaf = pyo.Var(model.vertices, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def degree_rule(network, vertex):
        return sum(
            network.selected[first, second]
            for first, second in incident_edges[vertex]
        )

    model.degree = pyo.Expression(model.vertices, rule=degree_rule)

    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.selected[edge] for edge in edges) == node_count - 1
    )

    def flow_capacity_rule(network, first, second):
        edge = edge_for_arc[first, second]
        return (
            network.flow[first, second]
            <= (node_count - 1) * network.selected[edge]
        )

    model.flow_capacity = pyo.Constraint(
        model.arcs, rule=flow_capacity_rule
    )

    def flow_balance_rule(network, vertex):
        outgoing = sum(network.flow[arc] for arc in outgoing_arcs[vertex])
        incoming = sum(network.flow[arc] for arc in incoming_arcs[vertex])
        supply = node_count - 1 if vertex == 0 else -1
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    def leaf_lower_rule(network, vertex):
        return network.degree[vertex] >= 2 - network.leaf[vertex]

    def leaf_upper_rule(network, vertex):
        return (
            network.degree[vertex]
            <= 1 + (node_count - 2) * (1 - network.leaf[vertex])
        )

    model.leaf_degree_lower = pyo.Constraint(
        model.vertices, rule=leaf_lower_rule
    )
    model.leaf_degree_upper = pyo.Constraint(
        model.vertices, rule=leaf_upper_rule
    )

    model.total_leaves = pyo.Objective(
        expr=sum(model.leaf[vertex] for vertex in nodes),
        sense=pyo.maximize,
    )

    failure_reason = "no_objective"
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution is available to load.
        # Success is determined solely by objective-value retrieval below.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_leaves))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}