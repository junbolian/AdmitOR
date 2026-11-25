# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":"{(i,j): i,j in V, i<j}","R":[[0,1],[0,3],[0,6],[1,5],[1,6],[2,3],[2,4],[5,7]],"S":"all nonempty subsets of V excluding node 0"},"params":{"distance[i,j]":"params[f'dist_{i}_{j}'] for (i,j) in E"},"variables":{"traversals[i,j]":"nonnegative integer for (i,j) in E","half_degree[v]":"nonnegative integer for v in V"},"constraints":["traversals[i,j] >= 1 for (i,j) in R","sum(traversals[i,j] for edges incident to v) = 2*half_degree[v] for v in V","sum(traversals[i,j] for edges with exactly one endpoint in T) >= 2 for T in S"],"objective":"minimize sum(distance[i,j]*traversals[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    edges = tuple(combinations(nodes, 2))
    required_edges = (
        (0, 1),
        (0, 3),
        (0, 6),
        (1, 5),
        (1, 6),
        (2, 3),
        (2, 4),
        (5, 7),
    )
    subsets = tuple(
        frozenset(subset)
        for size in range(1, len(nodes))
        for subset in combinations(nodes[1:], size)
    )

    distances = {
        (i, j): params[f"dist_{i}_{j}"]
        for i, j in edges
    }
    crossing_edges = {
        subset_id: tuple(
            (i, j)
            for i, j in edges
            if (i in subset) != (j in subset)
        )
        for subset_id, subset in enumerate(subsets)
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.cut_ids = pyo.Set(
        initialize=range(len(subsets)), ordered=True
    )
    model.distance = pyo.Param(
        model.edges, initialize=distances, within=pyo.Reals
    )

    # Undirected edge multiplicities describe an Eulerian multigraph.
    model.traversals = pyo.Var(
        model.edges, domain=pyo.NonNegativeIntegers
    )
    model.half_degree = pyo.Var(
        model.vertices, domain=pyo.NonNegativeIntegers
    )

    def required_service_rule(instance, i, j):
        return instance.traversals[i, j] >= 1

    model.required_service = pyo.Constraint(
        model.required_edges, rule=required_service_rule
    )

    # Even degrees permit balanced entry and exit in an Euler tour.
    def degree_balance_rule(instance, vertex):
        return sum(
            instance.traversals[i, j]
            for i, j in edges
            if vertex == i or vertex == j
        ) == 2 * instance.half_degree[vertex]

    model.degree_balance = pyo.Constraint(
        model.vertices, rule=degree_balance_rule
    )

    # Every node is incident to a required edge, so every non-root
    # subset must connect to the rest of the closed delivery tour.
    def connectivity_rule(instance, subset_id):
        return sum(
            instance.traversals[i, j]
            for i, j in crossing_edges[subset_id]
        ) >= 2

    model.connectivity = pyo.Constraint(
        model.cut_ids, rule=connectivity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.traversals[i, j]
            for i, j in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution is available to load.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}