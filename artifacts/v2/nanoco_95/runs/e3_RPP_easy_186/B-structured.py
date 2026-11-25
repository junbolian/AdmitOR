# IR: {"sets":{"N":"0..8","A":"{(i,j): i,j in N, i!=j}","R":"params.required_edge_set, undirected","D":"params.non_required_edge_set, undirected","T":"endpoints of R excluding depot 0"},"params":{"c":"params.distance_matrix","asym_forward":"params.asymmetric_pair_2_4","asym_reverse":"params.asymmetric_pair_4_2","edge_count":"params.num_graph_edges","required_count":"params.num_required_edges","required_ratio":"params.required_edge_ratio"},"variables":{"x[i,j]":"nonnegative integer traversal count, (i,j) in A","f[i,j]":"nonnegative continuous connectivity flow, (i,j) in A"},"constraints":["Input consistency: matrix dimensions, directional entries, edge sets, counts, and ratio agree.","For each {i,j} in R: x[i,j]+x[j,i]>=1.","For each i in N: sum_j x[i,j]=sum_j x[j,i].","For each (i,j) in A: f[i,j]<=|T|*x[i,j].","At depot: outgoing f minus incoming f equals |T|.","At each i!=0: incoming f minus outgoing f equals 1 if i in T, otherwise 0."],"objective":"minimize sum_(i,j in A) c[i,j]*x[i,j]","route":"Extract the depot-rooted Euler circuit from optimal traversal counts and expose its exact node sequence as solve.route; return only objective and status."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the directed-cost rural postman problem.

    Returns:
        {"objective": float, "status": "optimal"} on success.
        {"objective": None, "status": short_reason} on expected failure.

    After success, solve.route contains the exact optimal node sequence,
    including depot 0 at both ends. This preserves the required return schema.
    """
    solve.route = None

    distance_matrix = params["distance_matrix"]
    asymmetric_pair_2_4 = params["asymmetric_pair_2_4"]
    asymmetric_pair_4_2 = params["asymmetric_pair_4_2"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    required_edge_ratio = params["required_edge_ratio"]
    required_edge_set = params["required_edge_set"]
    non_required_edge_set = params["non_required_edge_set"]

    nodes = tuple(range(9))
    depot = 0
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    if len(distance_matrix) != len(nodes):
        return {"objective": None, "status": "invalid_matrix"}
    if any(len(row) != len(nodes) for row in distance_matrix):
        return {"objective": None, "status": "invalid_matrix"}

    costs = {
        (origin, destination): float(distance_matrix[origin][destination])
        for origin in nodes
        for destination in nodes
    }

    if any(not math.isfinite(value) for value in costs.values()):
        return {"objective": None, "status": "invalid_costs"}
    if any(costs[node, node] != 0 for node in nodes):
        return {"objective": None, "status": "invalid_diagonal"}
    if any(costs[arc] <= 0 for arc in arcs):
        return {"objective": None, "status": "invalid_costs"}

    if (
        costs[2, 4] != float(asymmetric_pair_2_4)
        or costs[4, 2] != float(asymmetric_pair_4_2)
    ):
        return {"objective": None, "status": "inconsistent_asymmetry"}

    def normalize_edges(raw_edges):
        normalized = []
        for edge in raw_edges:
            if len(edge) != 2:
                return None
            origin, destination = edge
            if (
                origin not in nodes
                or destination not in nodes
                or origin == destination
            ):
                return None
            normalized.append(
                (min(origin, destination), max(origin, destination))
            )
        if len(set(normalized)) != len(normalized):
            return None
        return tuple(sorted(normalized))

    required_edges = normalize_edges(required_edge_set)
    transit_edges = normalize_edges(non_required_edge_set)

    if required_edges is None or transit_edges is None:
        return {"objective": None, "status": "invalid_edge_sets"}
    if set(required_edges) & set(transit_edges):
        return {"objective": None, "status": "overlapping_edge_sets"}
    if len(required_edges) != num_required_edges:
        return {"objective": None, "status": "inconsistent_required_count"}

    infrastructure_edges = set(required_edges) | set(transit_edges)
    if len(infrastructure_edges) != num_graph_edges:
        return {"objective": None, "status": "inconsistent_edge_count"}
    if num_graph_edges <= 0:
        return {"objective": None, "status": "invalid_edge_count"}
    if not math.isclose(
        float(required_edge_ratio),
        len(required_edges) / len(infrastructure_edges),
        rel_tol=1e-9,
        abs_tol=1e-12,
    ):
        return {"objective": None, "status": "inconsistent_required_ratio"}

    required_nodes = {
        node
        for edge in required_edges
        for node in edge
        if node != depot
    }
    connectivity_demand = len(required_nodes)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={arc: costs[arc] for arc in arcs},
        within=pyo.PositiveReals,
    )

    model.traversals = pyo.Var(
        model.arcs, domain=pyo.NonNegativeIntegers
    )
    model.connectivity_flow = pyo.Var(
        model.arcs, domain=pyo.NonNegativeReals
    )

    def service_rule(instance, origin, destination):
        return (
            instance.traversals[origin, destination]
            + instance.traversals[destination, origin]
            >= 1
        )

    model.service_coverage = pyo.Constraint(
        model.required_edges, rule=service_rule
    )

    def traversal_balance_rule(instance, node):
        outgoing = sum(
            instance.traversals[node, neighbor]
            for neighbor in instance.nodes
            if neighbor != node
        )
        incoming = sum(
            instance.traversals[neighbor, node]
            for neighbor in instance.nodes
            if neighbor != node
        )
        return outgoing == incoming

    model.traversal_balance = pyo.Constraint(
        model.nodes, rule=traversal_balance_rule
    )

    def connectivity_capacity_rule(instance, origin, destination):
        return (
            instance.connectivity_flow[origin, destination]
            <= connectivity_demand
            * instance.traversals[origin, destination]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.arcs, rule=connectivity_capacity_rule
    )

    def connectivity_balance_rule(instance, node):
        incoming = sum(
            instance.connectivity_flow[neighbor, node]
            for neighbor in instance.nodes
            if neighbor != node
        )
        outgoing = sum(
            instance.connectivity_flow[node, neighbor]
            for neighbor in instance.nodes
            if neighbor != node
        )
        if node == depot:
            return outgoing - incoming == connectivity_demand
        return incoming - outgoing == (1 if node in required_nodes else 0)

    model.connectivity_balance = pyo.Constraint(
        model.nodes, rule=connectivity_balance_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.traversals[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi may raise before loading values when no feasible solution exists.
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    # The balanced, depot-connected traversal multigraph has an Euler circuit.
    # Positive costs exclude disconnected cycles from an optimal solution.
    remaining = {
        (origin, destination): int(
            round(pyo.value(model.traversals[origin, destination]))
        )
        for origin, destination in arcs
    }
    successors = {
        origin: [
            destination
            for destination in nodes
            if origin != destination
            and remaining[origin, destination] > 0
        ]
        for origin in nodes
    }

    traversal_count = sum(remaining.values())
    stack = [depot]
    circuit = []

    while stack:
        origin = stack[-1]
        while (
            successors[origin]
            and remaining[origin, successors[origin][-1]] == 0
        ):
            successors[origin].pop()

        if successors[origin]:
            destination = successors[origin][-1]
            remaining[origin, destination] -= 1
            stack.append(destination)
        else:
            circuit.append(stack.pop())

    circuit.reverse()

    if (
        len(circuit) != traversal_count + 1
        or circuit[0] != depot
        or circuit[-1] != depot
        or any(remaining.values())
    ):
        raise RuntimeError("Optimal traversal counts did not yield one depot circuit.")

    solve.route = circuit
    return {"objective": obj_val, "status": "optimal"}


solve.route = None