# IR: {"sets":{"V":"range(num_nodes)","E":"range(num_edges)","D":[0,1]},"params":{"num_nodes":"node count, at least 2","num_edges":"candidate edge count","edge_list":"undirected candidate edges indexed by E","coordinates":"fixed node metadata; no effect on objective or constraints","distance_matrix":"fixed link-length metadata; no effect on objective or constraints"},"variables":{"selected[e]":"binary","leaf[v]":"binary","flow[e,d]":"nonnegative continuous; d=0 follows edge_list[e], d=1 reverses it"},"constraints":["sum(selected[e] for e in E) = num_nodes - 1","degree[v] = sum(selected[e] for edges incident to v)","degree[v] >= 2 - leaf[v]","degree[v] <= 1 + (num_nodes - 2)*(1 - leaf[v])","flow[e,d] <= (num_nodes - 1)*selected[e]","outflow[v] - inflow[v] = num_nodes - 1 if v=0 else -1"],"objective":"maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_edges = params["num_edges"]
    edge_list = [tuple(edge) for edge in params["edge_list"]]
    coordinates = params["coordinates"]
    distance_matrix = params["distance_matrix"]

    if num_nodes < 2 or num_edges < 0:
        return {"objective": None, "status": "invalid_dimensions"}
    if len(edge_list) != num_edges:
        return {"objective": None, "status": "invalid_edge_count"}
    if len(coordinates) != num_nodes or any(
        len(point) != 2 for point in coordinates
    ):
        return {"objective": None, "status": "invalid_coordinates"}
    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        return {"objective": None, "status": "invalid_distance_matrix"}

    incident = {node: [] for node in range(num_nodes)}
    outgoing = {node: [] for node in range(num_nodes)}
    incoming = {node: [] for node in range(num_nodes)}
    seen_edges = set()

    for edge_id, endpoints in enumerate(edge_list):
        if len(endpoints) != 2:
            return {"objective": None, "status": "invalid_edge"}

        first, second = endpoints
        if (
            first not in incident
            or second not in incident
            or first == second
        ):
            return {"objective": None, "status": "invalid_edge"}

        undirected_edge = frozenset((first, second))
        if undirected_edge in seen_edges:
            return {"objective": None, "status": "duplicate_edge"}
        seen_edges.add(undirected_edge)

        incident[first].append(edge_id)
        incident[second].append(edge_id)

        outgoing[first].append((edge_id, 0))
        incoming[second].append((edge_id, 0))
        outgoing[second].append((edge_id, 1))
        incoming[first].append((edge_id, 1))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.routes = pyo.Set(initialize=range(num_edges), ordered=True)
    model.directions = pyo.Set(initialize=(0, 1), ordered=True)

    model.selected = pyo.Var(model.routes, domain=pyo.Binary)
    model.leaf = pyo.Var(model.nodes, domain=pyo.Binary)
    model.flow = pyo.Var(
        model.routes, model.directions, domain=pyo.NonNegativeReals
    )

    model.edge_count = pyo.Constraint(
        expr=pyo.quicksum(model.selected[edge_id] for edge_id in model.routes)
        == num_nodes - 1
    )

    def degree_rule(network, node):
        return pyo.quicksum(
            network.selected[edge_id] for edge_id in incident[node]
        )

    model.degree = pyo.Expression(model.nodes, rule=degree_rule)

    def leaf_lower_rule(network, node):
        return network.degree[node] >= 2 - network.leaf[node]

    model.leaf_lower = pyo.Constraint(model.nodes, rule=leaf_lower_rule)

    def leaf_upper_rule(network, node):
        return network.degree[node] <= (
            1 + (num_nodes - 2) * (1 - network.leaf[node])
        )

    model.leaf_upper = pyo.Constraint(model.nodes, rule=leaf_upper_rule)

    def flow_capacity_rule(network, edge_id, direction):
        return network.flow[edge_id, direction] <= (
            (num_nodes - 1) * network.selected[edge_id]
        )

    model.flow_capacity = pyo.Constraint(
        model.routes, model.directions, rule=flow_capacity_rule
    )

    def flow_balance_rule(network, node):
        outflow = pyo.quicksum(
            network.flow[edge_id, direction]
            for edge_id, direction in outgoing[node]
        )
        inflow = pyo.quicksum(
            network.flow[edge_id, direction]
            for edge_id, direction in incoming[node]
        )
        supply = num_nodes - 1 if node == 0 else -1
        return outflow - inflow == supply

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )

    model.total_leaves = pyo.Objective(
        expr=pyo.quicksum(model.leaf[node] for node in model.nodes),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this specific error when no solution can be loaded.
        # Unexpected runtime errors still propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_leaves))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}