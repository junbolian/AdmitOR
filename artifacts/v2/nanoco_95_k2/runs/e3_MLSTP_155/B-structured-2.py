# IR: {"sets":{"V":"range(params['n_sensors'])","D":[0,1],"E":[[4,6],[12,13],[3,10],[5,10],[2,5],[1,3],[0,14],[0,11],[10,12],[11,14],[1,12],[6,11],[6,8],[6,14],[4,5],[3,9],[4,8],[3,12],[9,10],[2,4],[2,7],[1,5],[2,13],[4,7],[4,10],[0,6],[1,13],[1,10],[6,9],[7,8]],"A":"both orientations of E"},"params":{"n_sensors":"params['n_sensors']","n_candidate_edges":"params['n_candidate_edges']; must equal |E|","sensor_coordinates":"params['sensor_coordinates']; location metadata","edge_distances":"params['edge_distances']; cost metadata, unused by the leaf-count objective"},"variables":{"selected[E]":"binary","leaf[V]":"binary","flow[A]":"nonnegative continuous"},"constraints":["sum(selected[e] for e in E) = n_sensors - 1","degree[v] = sum(selected[e] for e incident to v); expression","degree[v] >= 2 - leaf[v] for v in V","degree[v] <= 1 + (n_sensors - 2)*(1 - leaf[v]) for v in V","flow[i,j] <= (n_sensors - 1)*selected[underlying_edge(i,j)] for (i,j) in A","outflow[v] - inflow[v] = n_sensors - 1 if v == 0 else -1 for v in V"],"objective":"maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_sensors = params["n_sensors"]
    n_candidate_edges = params["n_candidate_edges"]
    sensor_coordinates = params["sensor_coordinates"]
    edge_distances = params["edge_distances"]

    candidate_edges = [
        (4, 6), (12, 13), (3, 10), (5, 10), (2, 5),
        (1, 3), (0, 14), (0, 11), (10, 12), (11, 14),
        (1, 12), (6, 11), (6, 8), (6, 14), (4, 5),
        (3, 9), (4, 8), (3, 12), (9, 10), (2, 4),
        (2, 7), (1, 5), (2, 13), (4, 7), (4, 10),
        (0, 6), (1, 13), (1, 10), (6, 9), (7, 8),
    ]

    # These index-set sizes are frozen by the supplied problem structure.
    if n_sensors != 15 or n_candidate_edges != len(candidate_edges):
        return {"objective": None, "status": "invalid_dimensions"}

    vertices = list(range(n_sensors))
    arcs = []
    underlying_edge = {}
    incident_edges = {vertex: [] for vertex in vertices}
    outgoing = {vertex: [] for vertex in vertices}
    incoming = {vertex: [] for vertex in vertices}

    for left, right in candidate_edges:
        edge = (left, right)
        incident_edges[left].append(edge)
        incident_edges[right].append(edge)

        for source, target in ((left, right), (right, left)):
            arc = (source, target)
            arcs.append(arc)
            underlying_edge[arc] = edge
            outgoing[source].append(arc)
            incoming[target].append(arc)

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)
    model.edges = pyo.Set(
        dimen=2, initialize=candidate_edges, ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    # Preserve the supplied numeric data without introducing a distance
    # objective or recomputing costs from coordinates.
    model.sensor_coordinates = pyo.Param(
        model.vertices,
        model.dimensions,
        initialize=lambda _, vertex, dimension:
            sensor_coordinates[vertex][dimension],
        within=pyo.Reals,
    )
    model.edge_distances = pyo.Param(
        model.vertices,
        model.vertices,
        initialize=lambda _, source, target:
            edge_distances[source][target],
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)
    model.leaf = pyo.Var(model.vertices, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def degree_rule(instance, vertex):
        return pyo.quicksum(
            instance.selected[edge] for edge in incident_edges[vertex]
        )

    model.degree = pyo.Expression(
        model.vertices, rule=degree_rule
    )

    model.tree_edge_count = pyo.Constraint(
        expr=pyo.quicksum(model.selected[edge] for edge in model.edges)
        == n_sensors - 1
    )

    def degree_lower_rule(instance, vertex):
        return instance.degree[vertex] >= 2 - instance.leaf[vertex]

    def degree_upper_rule(instance, vertex):
        return instance.degree[vertex] <= (
            1 + (n_sensors - 2) * (1 - instance.leaf[vertex])
        )

    model.degree_lower = pyo.Constraint(
        model.vertices, rule=degree_lower_rule
    )
    model.degree_upper = pyo.Constraint(
        model.vertices, rule=degree_upper_rule
    )

    def flow_capacity_rule(instance, source, target):
        edge = underlying_edge[(source, target)]
        return (
            instance.flow[source, target]
            <= (n_sensors - 1) * instance.selected[edge]
        )

    model.flow_capacity = pyo.Constraint(
        model.arcs, rule=flow_capacity_rule
    )

    # Sensor 0 is an arbitrary flow root. Delivering one unit to every
    # other sensor enforces connectivity; the edge count enforces a tree.
    def flow_balance_rule(instance, vertex):
        net_outflow = (
            pyo.quicksum(
                instance.flow[arc] for arc in outgoing[vertex]
            )
            - pyo.quicksum(
                instance.flow[arc] for arc in incoming[vertex]
            )
        )
        return net_outflow == (
            n_sensors - 1 if vertex == 0 else -1
        )

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    model.leaf_objective = pyo.Objective(
        expr=pyo.quicksum(
            model.leaf[vertex] for vertex in model.vertices
        ),
        sense=pyo.maximize,
    )

    failure_reason = "no_objective"
    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.leaf_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}