# IR: {"sets":{"V":"vertices a through j, with size params['num_vertices']","E":"range(params['num_edges'])","G":"outer cycle a-b-c-d-e-a, spokes a-f/b-g/c-h/d-i/e-j, and all pairs in {f,g,h,i,j}"},"params":{"num_vertices":"frozen vertex count; must match G","num_edges":"frozen edge count; must match G","edge_incidence_a":"binary vector indexed by E; identifies edges incident to a"},"edge_mapping":"Assign G's a-incident edges to E positions flagged 1 and remaining edges to positions flagged 0, preserving construction order within each group.","decision_variables":{"x[v]":"binary; 1 iff vertex v is selected"},"constraints":["For every e in E: sum(x[v] for v incident to e) >= 1."],"objective":"minimize sum(x[v] for v in V)"}

from itertools import combinations
from operator import index

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_vertices = index(params["num_vertices"])
    num_edges = index(params["num_edges"])
    edge_incidence_a = tuple(params["edge_incidence_a"])

    vertex_labels = tuple("abcdefghij")
    outer_vertices = tuple("abcde")
    inner_vertices = tuple("fghij")

    outer_edges = [
        (outer_vertices[position],
         outer_vertices[(position + 1) % len(outer_vertices)])
        for position in range(len(outer_vertices))
    ]
    spoke_edges = list(zip(outer_vertices, inner_vertices))
    inner_edges = list(combinations(inner_vertices, 2))
    graph_edges = outer_edges + spoke_edges + inner_edges

    if (
        num_vertices != len(vertex_labels)
        or num_edges != len(graph_edges)
    ):
        return {"objective": None, "status": "invalid_graph_dimensions"}

    if (
        len(edge_incidence_a) != num_edges
        or any(flag not in (0, 1) for flag in edge_incidence_a)
    ):
        return {"objective": None, "status": "invalid_incidence"}

    incident_edges = [edge for edge in graph_edges if "a" in edge]
    other_edges = [edge for edge in graph_edges if "a" not in edge]

    if sum(edge_incidence_a) != len(incident_edges):
        return {"objective": None, "status": "inconsistent_incidence"}

    # Only a's incidence vector is supplied. Its flagged positions determine
    # edge indexing; ordering within each group does not change the graph.
    incident_iterator = iter(incident_edges)
    other_iterator = iter(other_edges)
    edge_endpoints = {
        edge_id: next(incident_iterator) if flag else next(other_iterator)
        for edge_id, flag in enumerate(edge_incidence_a)
    }

    model = pyo.ConcreteModel()
    model.vertex_set = pyo.Set(
        initialize=vertex_labels[:num_vertices], ordered=True
    )
    model.edge_set = pyo.Set(initialize=range(num_edges), ordered=True)

    incidence_values = {
        (vertex, edge_id): (
            int(edge_incidence_a[edge_id])
            if vertex == "a"
            else int(vertex in edge_endpoints[edge_id])
        )
        for vertex in vertex_labels
        for edge_id in range(num_edges)
    }
    model.incidence = pyo.Param(
        model.vertex_set,
        model.edge_set,
        initialize=incidence_values,
        within=pyo.Binary,
    )
    model.selected = pyo.Var(model.vertex_set, domain=pyo.Binary)

    def cover_rule(instance, edge_id):
        return sum(
            instance.incidence[vertex, edge_id] * instance.selected[vertex]
            for vertex in instance.vertex_set
        ) >= 1

    model.edge_coverage = pyo.Constraint(
        model.edge_set, rule=cover_rule
    )
    model.cover_size = pyo.Objective(
        expr=sum(model.selected[vertex] for vertex in model.vertex_set),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "infeasible_or_failed"

    # Objective retrieval is the sole success criterion.
    try:
        obj_val = float(pyo.value(model.cover_size))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}