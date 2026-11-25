# IR: {"sets":{"V":"0..7","E":[[0,1],[0,3],[0,5],[0,6],[0,7],[1,2],[1,3],[1,4],[1,5],[1,6],[2,3],[2,4],[2,7],[3,4],[3,5],[4,5],[4,6],[4,7],[5,7],[6,7]]},"params":{"link_weights":"real[E], from params['link_weights'] in listed order","port_limits":"real[V], from params['port_limits']"},"variables":{"selected[e]":"binary, e in E"},"constraints":["For each v in V: sum(selected[e] for e incident to v) <= port_limits[v]"],"objective":"maximize sum(link_weights[e] * selected[e] for e in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 7),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 7), (6, 7),
    )

    model = pyo.ConcreteModel()
    model.vertices = pyo.RangeSet(0, 7)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)

    model.link_weights = pyo.Param(
        model.edges,
        initialize={
            edge: params["link_weights"][edge_index]
            for edge_index, edge in enumerate(edges)
        },
        within=pyo.Reals,
    )
    model.port_limits = pyo.Param(
        model.vertices,
        initialize={
            vertex: params["port_limits"][vertex]
            for vertex in range(8)
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)

    def port_capacity_rule(network, vertex):
        return (
            sum(
                network.selected[start, end]
                for start, end in edges
                if start == vertex or end == vertex
            )
            <= network.port_limits[vertex]
        )

    model.port_capacity = pyo.Constraint(
        model.vertices, rule=port_capacity_rule
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.link_weights[start, end] * model.selected[start, end]
            for start, end in edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}