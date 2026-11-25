# IR: {"sets":{"V":"{0,...,11}","E":"unique undirected edges from params['approved_edges']","A":"both orientations of every edge in E"},"params":{"distance_matrix":"params['distance_matrix']","approved_edges":"params['approved_edges']","weight[e]":"distance_matrix[e[0]][e[1]]","n":"|V|","root":"0"},"variables":{"selected[e]":"binary for e in E","flow[i,j]":"nonnegative continuous for (i,j) in A","leaf[v]":"binary for v in V"},"constraints":["sum(selected[e] for e in E) = n-1","sum(flow[v,j]) - sum(flow[i,v]) = n-1 if v=root, otherwise -1","flow[i,j] <= (n-1)*selected[canonical(i,j)] for (i,j) in A","degree[v] >= 2-leaf[v] for v in V","degree[v] <= (n-1)-(n-2)*leaf[v] for v in V"],"objective":"maximize sum(leaf[v] for v in V); distance weights are recorded but do not affect the leaf-count objective"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    approved_edges = params["approved_edges"]

    nodes = list(range(12))
    node_count = len(nodes)
    root = nodes[0]

    edges = sorted(
        {
            (min(endpoint_a, endpoint_b), max(endpoint_a, endpoint_b))
            for endpoint_a, endpoint_b in approved_edges
        }
    )

    if any(
        endpoint_a not in nodes
        or endpoint_b not in nodes
        or endpoint_a == endpoint_b
        for endpoint_a, endpoint_b in edges
    ):
        raise ValueError("Approved edges must join distinct nodes from 0 to 11.")

    arcs = [
        arc
        for endpoint_a, endpoint_b in edges
        for arc in (
            (endpoint_a, endpoint_b),
            (endpoint_b, endpoint_a),
        )
    ]

    incident_edges = {node: [] for node in nodes}
    outgoing_nodes = {node: [] for node in nodes}
    incoming_nodes = {node: [] for node in nodes}

    for endpoint_a, endpoint_b in edges:
        incident_edges[endpoint_a].append((endpoint_a, endpoint_b))
        incident_edges[endpoint_b].append((endpoint_a, endpoint_b))

    for source, destination in arcs:
        outgoing_nodes[source].append(destination)
        incoming_nodes[destination].append(source)

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.edge_weight = pyo.Param(
        model.edges,
        initialize={
            (endpoint_a, endpoint_b): distance_matrix[endpoint_a][endpoint_b]
            for endpoint_a, endpoint_b in edges
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.leaf = pyo.Var(model.vertices, domain=pyo.Binary)

    def degree_rule(network, node):
        return pyo.quicksum(
            network.selected[endpoint_a, endpoint_b]
            for endpoint_a, endpoint_b in incident_edges[node]
        )

    model.degree = pyo.Expression(model.vertices, rule=degree_rule)

    model.tree_edge_count = pyo.Constraint(
        expr=pyo.quicksum(model.selected[edge] for edge in model.edges)
        == node_count - 1
    )

    def flow_balance_rule(network, node):
        outgoing_flow = pyo.quicksum(
            network.flow[node, destination]
            for destination in outgoing_nodes[node]
        )
        incoming_flow = pyo.quicksum(
            network.flow[source, node]
            for source in incoming_nodes[node]
        )
        required_balance = node_count - 1 if node == root else -1
        # The binary term preserves a symbolic expression for isolated nodes.
        return (
            outgoing_flow - incoming_flow + 0 * network.leaf[node]
            == required_balance
        )

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    def flow_capacity_rule(network, source, destination):
        edge = (min(source, destination), max(source, destination))
        return (
            network.flow[source, destination]
            <= (node_count - 1) * network.selected[edge]
        )

    model.flow_capacity = pyo.Constraint(
        model.arcs, rule=flow_capacity_rule
    )

    def leaf_lower_rule(network, node):
        return network.degree[node] >= 2 - network.leaf[node]

    model.leaf_lower = pyo.Constraint(
        model.vertices, rule=leaf_lower_rule
    )

    def leaf_upper_rule(network, node):
        return (
            network.degree[node]
            <= (node_count - 1) - (node_count - 2) * network.leaf[node]
        )

    model.leaf_upper = pyo.Constraint(
        model.vertices, rule=leaf_upper_rule
    )

    model.total_leaves = pyo.Objective(
        expr=pyo.quicksum(model.leaf[node] for node in model.vertices),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_leaves))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}