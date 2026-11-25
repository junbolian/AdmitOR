# IR: {"sets":{"V":"{0,...,11}","E":"unique undirected pairs (i,j), i<j, from params['approved_edges']","A":"both orientations of E"},"params":{"distance_matrix":"params['distance_matrix']; edge weights, with no role in the leaf-count objective","approved_edges":"params['approved_edges']","n":"|V|"},"variables":{"x[e]":"Binary; select edge e","leaf[v]":"Binary; node v has degree exactly one","flow[i,j]":"NonNegativeReals; connectivity flow on directed arc (i,j)"},"expressions":{"degree[v]":"sum(x[e] for edges incident to v)"},"constraints":["sum(x[e] for e in E) = n-1","sum(flow[v,j]) - sum(flow[i,v]) = n-1 if v=0, else -1","flow[i,j] <= (n-1)*x[min(i,j),max(i,j)] for every arc","degree[v] >= 2-leaf[v]","degree[v] <= (n-1)-(n-2)*leaf[v]"],"objective":"maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    approved_edges = params["approved_edges"]

    nodes = list(range(12))
    node_count = len(nodes)
    node_set = set(nodes)

    normalized_edges = set()
    for first, second in approved_edges:
        if first not in node_set or second not in node_set:
            raise ValueError("Approved edge contains an invalid node index.")
        if first == second:
            raise ValueError("Approved edges must not contain self-loops.")
        normalized_edges.add((min(first, second), max(first, second)))

    edges = sorted(normalized_edges)
    arcs = sorted(
        directed_edge
        for first, second in edges
        for directed_edge in ((first, second), (second, first))
    )

    incident_edges = {node: [] for node in nodes}
    outgoing_nodes = {node: [] for node in nodes}
    incoming_nodes = {node: [] for node in nodes}

    for first, second in edges:
        incident_edges[first].append((first, second))
        incident_edges[second].append((first, second))

    for first, second in arcs:
        outgoing_nodes[first].append(second)
        incoming_nodes[second].append(first)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(
        initialize=edges,
        dimen=2,
        within=model.nodes * model.nodes,
        ordered=True,
    )
    model.arcs = pyo.Set(
        initialize=arcs,
        dimen=2,
        within=model.nodes * model.nodes,
        ordered=True,
    )

    # Latency weights are retained as input data. The requested objective
    # maximizes leaves and does not minimize latency or use a latency tie-break.
    model.edge_weight = pyo.Param(
        model.edges,
        initialize={
            (first, second): distance_matrix[first][second]
            for first, second in edges
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.edges, domain=pyo.Binary)
    model.leaf = pyo.Var(model.nodes, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def degree_rule(network, node):
        return sum(
            (network.x[edge] for edge in incident_edges[node]),
            0 * network.leaf[node],
        )

    model.degree = pyo.Expression(model.nodes, rule=degree_rule)

    # The zero term keeps the constraint symbolic even if E is empty.
    model.tree_edge_count = pyo.Constraint(
        expr=sum(
            (model.x[edge] for edge in edges),
            0 * model.leaf[0],
        )
        == node_count - 1
    )

    def flow_balance_rule(network, node):
        outgoing = sum(
            (network.flow[node, other] for other in outgoing_nodes[node]),
            0 * network.leaf[node],
        )
        incoming = sum(
            network.flow[other, node] for other in incoming_nodes[node]
        )
        required_balance = node_count - 1 if node == 0 else -1
        return outgoing - incoming == required_balance

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )

    def flow_capacity_rule(network, first, second):
        edge = (min(first, second), max(first, second))
        return network.flow[first, second] <= (
            node_count - 1
        ) * network.x[edge]

    model.flow_capacity = pyo.Constraint(
        model.arcs,
        rule=flow_capacity_rule,
    )

    def leaf_degree_lower_rule(network, node):
        return network.degree[node] >= 2 - network.leaf[node]

    model.leaf_degree_lower = pyo.Constraint(
        model.nodes,
        rule=leaf_degree_lower_rule,
    )

    def leaf_degree_upper_rule(network, node):
        return network.degree[node] <= (
            node_count - 1
        ) - (node_count - 2) * network.leaf[node]

    model.leaf_degree_upper = pyo.Constraint(
        model.nodes,
        rule=leaf_degree_upper_rule,
    )

    model.leaf_objective = pyo.Objective(
        expr=sum(model.leaf[node] for node in model.nodes),
        sense=pyo.maximize,
    )

    # APPsi raises this RuntimeError when it cannot load a feasible solution.
    # Unexpected solver exceptions propagate to the calling harness.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.leaf_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}