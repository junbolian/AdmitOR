# IR: {"sets":{"V":"range(n_sensors)","E":"the 30 specified undirected candidate edges","A":"both orientations of E","K":[0,1]},"params":{"n_sensors":"params['n_sensors']; frozen at 15","n_candidate_edges":"params['n_candidate_edges']; frozen at 30","coordinates[v,k]":"params['sensor_coordinates'][v][k]; descriptive data","distance[i,j]":"params['edge_distances'][i][j]; descriptive cost data, excluded from the leaf-count objective"},"variables":{"selected[e]":"binary for e in E","leaf[v]":"binary for v in V","flow[i,j]":"nonnegative real for (i,j) in A"},"constraints":{"tree_size":"sum(selected[e] for e in E) = n_sensors - 1","flow_capacity":"flow[i,j] <= (n_sensors - 1) * selected[undirected(i,j)] for (i,j) in A","connectivity":"outflow[v] - inflow[v] = n_sensors - 1 if v = 0, otherwise -1","leaf_degree_upper":"degree[v] <= 1 + (n_sensors - 2) * (1 - leaf[v])","leaf_degree_lower":"degree[v] >= 2 - leaf[v]"},"objective":"maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_sensors = int(params["n_sensors"])
    n_candidate_edges = int(params["n_candidate_edges"])
    sensor_coordinates = params["sensor_coordinates"]
    edge_distances = params["edge_distances"]

    candidate_edges = [
        (4, 6),
        (12, 13),
        (3, 10),
        (5, 10),
        (2, 5),
        (1, 3),
        (0, 14),
        (0, 11),
        (10, 12),
        (11, 14),
        (1, 12),
        (6, 11),
        (6, 8),
        (6, 14),
        (4, 5),
        (3, 9),
        (4, 8),
        (3, 12),
        (9, 10),
        (2, 4),
        (2, 7),
        (1, 5),
        (2, 13),
        (4, 7),
        (4, 10),
        (0, 6),
        (1, 13),
        (1, 10),
        (6, 9),
        (7, 8),
    ]

    # These sizes are structural constants of the specified instance.
    if n_sensors != 15 or n_candidate_edges != len(candidate_edges):
        return {"objective": None, "status": "invalid_dimensions"}

    vertices = list(range(n_sensors))
    arcs = []
    arc_to_edge = {}
    neighbors = {vertex: [] for vertex in vertices}
    incident_edges = {vertex: [] for vertex in vertices}

    for first, second in candidate_edges:
        arcs.extend([(first, second), (second, first)])
        arc_to_edge[first, second] = (first, second)
        arc_to_edge[second, first] = (first, second)
        neighbors[first].append(second)
        neighbors[second].append(first)
        incident_edges[first].append((first, second))
        incident_edges[second].append((first, second))

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.candidate_edges = pyo.Set(
        dimen=2, initialize=candidate_edges, ordered=True
    )
    model.directed_arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.coordinate_axes = pyo.Set(initialize=[0, 1], ordered=True)

    model.sensor_count = pyo.Param(
        initialize=n_sensors, within=pyo.PositiveIntegers
    )
    model.candidate_count = pyo.Param(
        initialize=n_candidate_edges, within=pyo.PositiveIntegers
    )
    model.coordinates = pyo.Param(
        model.vertices,
        model.coordinate_axes,
        initialize=lambda mdl, vertex, axis: sensor_coordinates[vertex][axis],
        within=pyo.Reals,
    )
    model.distances = pyo.Param(
        model.vertices,
        model.vertices,
        initialize=lambda mdl, first, second: edge_distances[first][second],
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.candidate_edges, domain=pyo.Binary)
    model.leaf = pyo.Var(model.vertices, domain=pyo.Binary)
    model.flow = pyo.Var(model.directed_arcs, domain=pyo.NonNegativeReals)

    def degree_rule(mdl, vertex):
        return pyo.quicksum(
            mdl.selected[first, second]
            for first, second in incident_edges[vertex]
        )

    model.degree = pyo.Expression(model.vertices, rule=degree_rule)

    model.tree_size = pyo.Constraint(
        expr=pyo.quicksum(
            model.selected[first, second]
            for first, second in model.candidate_edges
        )
        == model.sensor_count - 1
    )

    def flow_capacity_rule(mdl, first, second):
        edge = arc_to_edge[first, second]
        return (
            mdl.flow[first, second]
            <= (mdl.sensor_count - 1) * mdl.selected[edge]
        )

    model.flow_capacity = pyo.Constraint(
        model.directed_arcs, rule=flow_capacity_rule
    )

    def connectivity_rule(mdl, vertex):
        outflow = pyo.quicksum(
            mdl.flow[vertex, neighbor] for neighbor in neighbors[vertex]
        )
        inflow = pyo.quicksum(
            mdl.flow[neighbor, vertex] for neighbor in neighbors[vertex]
        )
        required_balance = mdl.sensor_count - 1 if vertex == 0 else -1
        return outflow - inflow == required_balance

    model.connectivity = pyo.Constraint(
        model.vertices, rule=connectivity_rule
    )

    def leaf_degree_upper_rule(mdl, vertex):
        return (
            mdl.degree[vertex]
            <= 1 + (mdl.sensor_count - 2) * (1 - mdl.leaf[vertex])
        )

    def leaf_degree_lower_rule(mdl, vertex):
        return mdl.degree[vertex] >= 2 - mdl.leaf[vertex]

    model.leaf_degree_upper = pyo.Constraint(
        model.vertices, rule=leaf_degree_upper_rule
    )
    model.leaf_degree_lower = pyo.Constraint(
        model.vertices, rule=leaf_degree_lower_rule
    )

    model.leaf_objective = pyo.Objective(
        expr=pyo.quicksum(model.leaf[vertex] for vertex in model.vertices),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.leaf_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}