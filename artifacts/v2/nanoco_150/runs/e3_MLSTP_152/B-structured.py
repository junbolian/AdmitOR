# IR: {"sets":{"V":"0..11","E":"indices of params['available_edges'], preserving every pair","D":[0,1],"C":[0,1]},"params":{"available_edges":"fixed undirected edge endpoints","coords":"params['coords'][v][c], geographic metadata","distance_matrix":"params['distance_matrix'][u][v], distance metadata"},"variables":{"x[e]":"binary; edge selected","leaf[v]":"binary; degree equals one","flow[e,d]":"nonnegative continuous; d=0 follows listed endpoints, d=1 reverses them"},"expressions":{"degree[v]":"sum of x[e] over incident edges"},"constraints":["sum_e x[e] = |V|-1","outflow[v]-inflow[v] = |V|-1 at root 0, otherwise -1","flow[e,d] <= (|V|-1)*x[e]","degree[v] >= 2-leaf[v]","degree[v] <= (|V|-1)-(|V|-2)*leaf[v]"],"objective":"maximize sum_v leaf[v]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    available_edges = params["available_edges"]
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    num_nodes = 12
    nodes = range(num_nodes)
    edge_ids = range(len(available_edges))
    endpoints = {
        edge_id: (pair[0], pair[1])
        for edge_id, pair in enumerate(available_edges)
    }

    incident_edges = {node: [] for node in nodes}
    outgoing_arcs = {node: [] for node in nodes}
    incoming_arcs = {node: [] for node in nodes}

    for edge_id in edge_ids:
        source, target = endpoints[edge_id]
        incident_edges[source].append(edge_id)
        incident_edges[target].append(edge_id)
        outgoing_arcs[source].append((edge_id, 0))
        incoming_arcs[target].append((edge_id, 0))
        outgoing_arcs[target].append((edge_id, 1))
        incoming_arcs[source].append((edge_id, 1))

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(initialize=edge_ids, ordered=True)
    model.D = pyo.Set(initialize=[0, 1], ordered=True)
    model.C = pyo.Set(initialize=[0, 1], ordered=True)

    # Retain the supplied geographic data. The objective counts leaves,
    # so neither coordinates nor distances enter the objective.
    model.coords = pyo.Param(
        model.V,
        model.C,
        initialize={
            (node, coordinate): coords[node][coordinate]
            for node in nodes
            for coordinate in range(2)
        },
        within=pyo.Reals,
    )
    model.distance_matrix = pyo.Param(
        model.V,
        model.V,
        initialize={
            (source, target): distance_matrix[source][target]
            for source in nodes
            for target in nodes
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.leaf = pyo.Var(model.V, domain=pyo.Binary)
    model.flow = pyo.Var(model.E, model.D, domain=pyo.NonNegativeReals)

    def degree_rule(instance, node):
        return pyo.quicksum(
            instance.x[edge_id] for edge_id in incident_edges[node]
        )

    model.degree = pyo.Expression(model.V, rule=degree_rule)

    model.tree_edge_count = pyo.Constraint(
        expr=pyo.quicksum(model.x[edge_id] for edge_id in model.E)
        == num_nodes - 1
    )

    def balance_rule(instance, node):
        outgoing = pyo.quicksum(
            instance.flow[edge_id, direction]
            for edge_id, direction in outgoing_arcs[node]
        )
        incoming = pyo.quicksum(
            instance.flow[edge_id, direction]
            for edge_id, direction in incoming_arcs[node]
        )
        supply = num_nodes - 1 if node == 0 else -1
        return outgoing - incoming == supply

    model.flow_balance = pyo.Constraint(model.V, rule=balance_rule)

    def capacity_rule(instance, edge_id, direction):
        return (
            instance.flow[edge_id, direction]
            <= (num_nodes - 1) * instance.x[edge_id]
        )

    model.flow_capacity = pyo.Constraint(
        model.E, model.D, rule=capacity_rule
    )

    def leaf_lower_rule(instance, node):
        return instance.degree[node] >= 2 - instance.leaf[node]

    model.leaf_lower = pyo.Constraint(model.V, rule=leaf_lower_rule)

    def leaf_upper_rule(instance, node):
        return (
            instance.degree[node]
            <= (num_nodes - 1) - (num_nodes - 2) * instance.leaf[node]
        )

    model.leaf_upper = pyo.Constraint(model.V, rule=leaf_upper_rule)

    model.total_leaves = pyo.Objective(
        expr=pyo.quicksum(model.leaf[node] for node in model.V),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_leaves))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}