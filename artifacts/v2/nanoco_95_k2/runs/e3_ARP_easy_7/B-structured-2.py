# IR: {"sets":{"V":"{0,...,7}","D":"{0,1}","A":"{(i,j) in V x V: i != j}","R":[[0,2],[0,6],[1,3],[1,6],[2,4],[2,7],[3,5],[3,7]],"S":"all nonempty subsets of V excluding depot 0"},"params":{"coords":"real coordinates indexed by V x D, read from params['coords']","distance_matrix":"nonnegative travel distances indexed by A, read from params['distance_matrix']"},"variables":{"x[i,j]":"nonnegative integer traversal count for each (i,j) in A"},"constraints":["Required coverage: x[i,j] + x[j,i] >= 1 for every (i,j) in R.","Flow balance: sum_j x[i,j] = sum_j x[j,i] for every i in V, excluding self-arcs.","Depot connectivity: sum_{i in S,j outside S} x[i,j] >= 1 for every nonempty S subset of V excluding depot 0."],"objective":"minimize sum_{(i,j) in A} distance_matrix[i,j] * x[i,j]"}
from itertools import combinations

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    nodes = tuple(range(8))
    required_segments = (
        (0, 2),
        (0, 6),
        (1, 3),
        (1, 6),
        (2, 4),
        (2, 7),
        (3, 5),
        (3, 7),
    )

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in nodes
            for j in nodes
            if i != j
        ],
    )
    model.required_segments = pyo.Set(
        dimen=2, initialize=required_segments
    )

    model.coordinates = pyo.Param(
        model.vertices,
        model.coordinate_axes,
        initialize=lambda mdl, i, axis: coords[i][axis],
        within=pyo.Reals,
    )
    model.travel_distance = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.traversals = pyo.Var(
        model.arcs, domain=pyo.NonNegativeIntegers
    )

    def coverage_rule(mdl, i, j):
        return mdl.traversals[i, j] + mdl.traversals[j, i] >= 1

    model.required_coverage = pyo.Constraint(
        model.required_segments, rule=coverage_rule
    )

    def flow_balance_rule(mdl, i):
        return (
            sum(mdl.traversals[i, j] for j in nodes if j != i)
            == sum(mdl.traversals[j, i] for j in nodes if j != i)
        )

    model.flow_balance = pyo.Constraint(
        model.vertices, rule=flow_balance_rule
    )

    # Every vertex is incident to a required segment. These cuts connect
    # every visited component to the depot; flow balance then guarantees
    # that the traversal multigraph admits a closed Euler tour.
    model.depot_connectivity = pyo.ConstraintList()
    nondepot_nodes = tuple(i for i in nodes if i != 0)
    for subset_size in range(1, len(nondepot_nodes) + 1):
        for subset in combinations(nondepot_nodes, subset_size):
            subset_members = frozenset(subset)
            model.depot_connectivity.add(
                sum(
                    model.traversals[i, j]
                    for i in subset
                    for j in nodes
                    if j not in subset_members
                )
                >= 1
            )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.traversals[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        solver_failed = True

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}