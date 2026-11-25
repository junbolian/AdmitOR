# IR: {"sets":{"V":"0..7","A":"all ordered pairs of distinct nodes","E":"(0,2),(0,3),(0,5),(0,7),(1,3),(2,6),(2,7),(4,5),(5,7)","R":"(0,2),(0,3),(0,5),(0,7),(2,6),(4,5),(5,7)","T":"endpoints of R together with depot 0"},"params":{"distance_matrix":"params['distance_matrix']; accept 56 row-major off-diagonal values, 64 row-major values including diagonal, or an 8x8 nested matrix; normalize to c[i,j]","coordinates_x":"params['coordinates_x']; eight geographic metadata values","coordinates_y":"params['coordinates_y']; eight geographic metadata values","required_edge_ratio":"params['required_edge_ratio']; descriptive metadata, with explicit R defining coverage","U":"|R|+(|R|+1)(|V|-1)"},"variables":{"x[i,j]":"nonnegative integer traversal count on A","y[i]":"binary node-use indicator on V","f[i,j]":"nonnegative continuous connectivity flow on A"},"constraints":["sum_j x[i,j] = sum_j x[j,i] for every i","x[i,j]+x[j,i] >= 1 for every (i,j) in R","y[i] = 1 for every i in T","x[i,j] <= U*y[i] for every (i,j) in A","x[i,j] <= U*y[j] for every (i,j) in A","f[i,j] <= (|V|-1)*x[i,j] for every (i,j) in A","sum_j f[j,i]-sum_j f[i,j] = y[i] for every i != 0","sum_j f[0,j]-sum_j f[j,0] = sum_{i!=0} y[i]"],"objective":"minimize sum_{(i,j) in A} c[i,j]*x[i,j]"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the depot-connected required-edge routing problem."""
    nodes = tuple(range(8))
    depot = 0
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    physical_edges = (
        (0, 2), (0, 3), (0, 5), (0, 7), (1, 3),
        (2, 6), (2, 7), (4, 5), (5, 7),
    )
    required_edges = (
        (0, 2), (0, 3), (0, 5), (0, 7),
        (2, 6), (4, 5), (5, 7),
    )
    mandatory_nodes = sorted(
        {depot}.union(
            node for edge in required_edges for node in edge
        )
    )
    non_depot_nodes = tuple(node for node in nodes if node != depot)

    raw_distances = list(params["distance_matrix"])
    raw_coordinates_x = list(params["coordinates_x"])
    raw_coordinates_y = list(params["coordinates_y"])
    raw_required_edge_ratio = params["required_edge_ratio"]

    if (
        len(raw_coordinates_x) != len(nodes)
        or len(raw_coordinates_y) != len(nodes)
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    # Normalize both full-matrix and off-diagonal input representations.
    if len(raw_distances) == len(nodes):
        if not all(
            hasattr(row, "__iter__") and not isinstance(row, (str, bytes))
            for row in raw_distances
        ):
            return {"objective": None, "status": "invalid_dimensions"}
        matrix_rows = [list(row) for row in raw_distances]
        if any(len(row) != len(nodes) for row in matrix_rows):
            return {"objective": None, "status": "invalid_dimensions"}
        raw_distances = [
            value for row in matrix_rows for value in row
        ]

    if len(raw_distances) not in (len(arcs), len(nodes) ** 2):
        return {"objective": None, "status": "invalid_dimensions"}

    try:
        distances = [float(value) for value in raw_distances]
        coordinates_x = [float(value) for value in raw_coordinates_x]
        coordinates_y = [float(value) for value in raw_coordinates_y]
        required_edge_ratio = float(raw_required_edge_ratio)
    except (TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_numeric_input"}

    if any(not math.isfinite(value) or value < 0 for value in distances):
        return {"objective": None, "status": "invalid_distances"}

    if any(
        not math.isfinite(value)
        for value in coordinates_x + coordinates_y
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    if (
        not math.isfinite(required_edge_ratio)
        or not 0 <= required_edge_ratio <= 1
    ):
        return {"objective": None, "status": "invalid_required_edge_ratio"}

    if len(distances) == len(nodes) ** 2:
        if any(
            distances[node * len(nodes) + node] != 0
            for node in nodes
        ):
            return {"objective": None, "status": "invalid_diagonal"}
        costs = {
            (origin, destination):
                distances[origin * len(nodes) + destination]
            for origin, destination in arcs
        }
    else:
        costs = dict(zip(arcs, distances))

    if any(
        costs[origin, destination] != costs[destination, origin]
        for origin, destination in arcs
    ):
        return {"objective": None, "status": "asymmetric_distances"}

    # Coordinates and the rounded required-edge ratio are descriptive.
    # The explicitly specified required edges determine service obligations.
    #
    # With nonnegative costs, an optimum can retain one service traversal
    # per required edge and at most |R|+1 simple connecting paths.
    traversal_bound = (
        len(required_edges)
        + (len(required_edges) + 1) * (len(nodes) - 1)
    )

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=physical_edges)
    model.R = pyo.Set(dimen=2, initialize=required_edges)
    model.T = pyo.Set(initialize=mandatory_nodes)
    model.non_depot_nodes = pyo.Set(initialize=non_depot_nodes)

    model.travel_cost = pyo.Param(model.A, initialize=costs)
    model.U = pyo.Param(initialize=traversal_bound)

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.V, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def route_balance_rule(instance, node):
        return (
            sum(
                instance.x[node, other]
                for other in nodes if other != node
            )
            == sum(
                instance.x[other, node]
                for other in nodes if other != node
            )
        )

    model.route_balance = pyo.Constraint(
        model.V, rule=route_balance_rule
    )

    model.service_coverage = pyo.Constraint(
        model.R,
        rule=lambda instance, origin, destination: (
            instance.x[origin, destination]
            + instance.x[destination, origin] >= 1
        ),
    )

    model.mandatory_node_use = pyo.Constraint(
        model.T,
        rule=lambda instance, node: instance.y[node] == 1,
    )

    model.origin_activation = pyo.Constraint(
        model.A,
        rule=lambda instance, origin, destination: (
            instance.x[origin, destination]
            <= instance.U * instance.y[origin]
        ),
    )

    model.destination_activation = pyo.Constraint(
        model.A,
        rule=lambda instance, origin, destination: (
            instance.x[origin, destination]
            <= instance.U * instance.y[destination]
        ),
    )

    model.connectivity_capacity = pyo.Constraint(
        model.A,
        rule=lambda instance, origin, destination: (
            instance.f[origin, destination]
            <= (len(nodes) - 1) * instance.x[origin, destination]
        ),
    )

    def connectivity_demand_rule(instance, node):
        return (
            sum(
                instance.f[other, node]
                for other in nodes if other != node
            )
            - sum(
                instance.f[node, other]
                for other in nodes if other != node
            )
            == instance.y[node]
        )

    model.connectivity_demand = pyo.Constraint(
        model.non_depot_nodes, rule=connectivity_demand_rule
    )

    model.depot_connectivity_supply = pyo.Constraint(
        expr=(
            sum(model.f[depot, node] for node in non_depot_nodes)
            - sum(model.f[node, depot] for node in non_depot_nodes)
            == sum(model.y[node] for node in non_depot_nodes)
        )
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    # Connectivity and balanced integer traversals ensure a closed Euler
    # tour through the depot covering every required undirected segment.
    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when it cannot load a feasible solution.
        # Success is determined exclusively by objective retrieval below.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}