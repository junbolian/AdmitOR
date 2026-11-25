# IR: {"sets":{"V":"0..14","E":"30 candidate undirected edges listed below","A":"both orientations of E"},"params":{"distance_matrix":"params['distance_matrix']; candidate-edge costs recorded but not used in the leaf-count objective","root":0,"N":"|V|"},"variables":{"selected[e]":"binary","leaf[v]":"binary","flow[i,j]":"nonnegative continuous"},"constraints":["sum(selected[e] for e in E) = N-1","degree[v] = sum(selected[e] for e incident to v)","degree[v] >= 2-leaf[v] for each v","degree[v] <= N-1-(N-2)*leaf[v] for each v","flow[i,j] <= (N-1)*selected[underlying_edge(i,j)] for each arc","outflow[v]-inflow[v] = N-1 if v=root, else -1"],"objective":"maximize sum(leaf[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]

    vertices = tuple(range(15))
    edges = (
        (4, 6), (12, 13), (3, 10), (5, 10), (2, 5),
        (1, 3), (0, 14), (0, 11), (10, 12), (11, 14),
        (1, 12), (6, 11), (6, 8), (6, 14), (4, 5),
        (3, 9), (4, 8), (3, 12), (9, 10), (2, 4),
        (2, 7), (1, 5), (2, 13), (4, 7), (4, 10),
        (0, 6), (1, 13), (1, 10), (6, 9), (7, 8),
    )
    arcs = tuple(
        arc
        for source, target in edges
        for arc in ((source, target), (target, source))
    )
    underlying_edge = {
        arc: (source, target)
        for source, target in edges
        for arc in ((source, target), (target, source))
    }
    incident_edges = {
        vertex: tuple(edge for edge in edges if vertex in edge)
        for vertex in vertices
    }
    neighbors = {
        vertex: tuple(target for source, target in arcs if source == vertex)
        for vertex in vertices
    }

    node_count = len(vertices)
    root = 0

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    # Distances are input data; the stated objective has no cost term.
    model.edge_cost = pyo.Param(
        model.E,
        initialize={
            (source, target): distance_matrix[source][target]
            for source, target in edges
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.E, domain=pyo.Binary)
    model.leaf = pyo.Var(model.V, domain=pyo.Binary)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    model.degree = pyo.Expression(
        model.V,
        rule=lambda mdl, vertex: sum(
            mdl.selected[edge] for edge in incident_edges[vertex]
        ),
    )

    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.selected[edge] for edge in model.E) == node_count - 1
    )

    model.degree_lower = pyo.Constraint(
        model.V,
        rule=lambda mdl, vertex: mdl.degree[vertex] >= 2 - mdl.leaf[vertex],
    )
    model.degree_upper = pyo.Constraint(
        model.V,
        rule=lambda mdl, vertex: (
            mdl.degree[vertex]
            <= node_count - 1 - (node_count - 2) * mdl.leaf[vertex]
        ),
    )

    model.flow_capacity = pyo.Constraint(
        model.A,
        rule=lambda mdl, source, target: (
            mdl.flow[source, target]
            <= (node_count - 1)
            * mdl.selected[underlying_edge[source, target]]
        ),
    )

    def flow_balance_rule(mdl, vertex):
        outflow = sum(mdl.flow[vertex, other] for other in neighbors[vertex])
        inflow = sum(mdl.flow[other, vertex] for other in neighbors[vertex])
        supply = node_count - 1 if vertex == root else -1
        return outflow - inflow == supply

    model.flow_balance = pyo.Constraint(model.V, rule=flow_balance_rule)

    model.leaf_objective = pyo.Objective(
        expr=sum(model.leaf[vertex] for vertex in model.V),
        sense=pyo.maximize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI can raise when no feasible solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.leaf_objective))
    except (ValueError, TypeError):
        reason = "solve_failed" if solve_failed else "objective_unavailable"
        return {"objective": None, "status": reason}

    return {"objective": obj_val, "status": "optimal"}