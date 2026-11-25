# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j): i,j in N, i != j}","R":[[0,1],[0,5],[1,5],[1,6],[2,3],[4,6]],"S":"all nonempty subsets of N excluding depot 0"},"params":{"distance_matrix":"params['distance_matrix']; direct travel costs indexed by origin and destination"},"variables":{"x[i,j]":"nonnegative integer traversal count for (i,j) in A"},"constraints":{"service":"x[i,j]+x[j,i] >= 1 for each (i,j) in R","flow_balance":"sum_j x[i,j] = sum_j x[j,i] for each i in N, excluding self-arcs","depot_connectivity":"sum_{i in U,j in N\\U} x[i,j] >= 1 for every U in S"},"objective":"minimize sum_{(i,j) in A} distance_matrix[i][j]*x[i,j]"}
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]

    nodes = tuple(range(7))
    nondepot_nodes = nodes[1:]
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    required_edges = (
        (0, 1),
        (0, 5),
        (1, 5),
        (1, 6),
        (2, 3),
        (4, 6),
    )

    model = pyo.ConcreteModel()
    model.junctions = pyo.Set(initialize=nodes, ordered=True)
    model.travel_arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.required_segments = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.travel_cost = pyo.Param(
        model.travel_arcs,
        initialize={
            (origin, destination): distance_matrix[origin][destination]
            for origin, destination in arcs
        },
    )
    model.traversals = pyo.Var(
        model.travel_arcs, domain=pyo.NonNegativeIntegers
    )

    def service_rule(route_model, origin, destination):
        return (
            route_model.traversals[origin, destination]
            + route_model.traversals[destination, origin]
            >= 1
        )

    model.segment_service = pyo.Constraint(
        model.required_segments, rule=service_rule
    )

    def flow_balance_rule(route_model, junction):
        departures = sum(
            route_model.traversals[junction, destination]
            for destination in nodes
            if destination != junction
        )
        arrivals = sum(
            route_model.traversals[origin, junction]
            for origin in nodes
            if origin != junction
        )
        return departures == arrivals

    model.junction_balance = pyo.Constraint(
        model.junctions, rule=flow_balance_rule
    )

    # Every junction is incident to a required segment in this instance.
    # These cuts therefore connect every visited junction to the depot.
    # Together with integer traversal counts and flow balance, they ensure
    # the selected arcs admit a single closed inspection circuit.
    model.depot_connectivity = pyo.ConstraintList()
    for subset_size in range(1, len(nondepot_nodes) + 1):
        for subset in combinations(nondepot_nodes, subset_size):
            subset_members = frozenset(subset)
            model.depot_connectivity.add(
                sum(
                    model.traversals[origin, destination]
                    for origin in subset
                    for destination in nodes
                    if destination not in subset_members
                )
                >= 1
            )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.traversals[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    # Appsi raises RuntimeError when no feasible solution can be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    # Success is determined solely by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}