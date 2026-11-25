# IR: {"sets":{"N":[0,1,2,3,4,5],"D":[0,1],"E":[[0,3],[0,4],[1,4],[2,3],[2,5],[3,4],[4,5]],"A":"both directions of E"},"params":{"coordinates":"real[N,D], fixed network geometry only","service_costs":"nonnegative[E], supplied in E order","distance_matrix":"nonnegative[N,N], supplied as 6x6 matrix or 15 upper-triangular entries in row-major order"},"variables":{"service":"nonnegative integer[A]","deadhead":"nonnegative integer[A]"},"constraints":["service[i,j]+service[j,i]>=1 for each (i,j) in E","sum(service[i,j]+deadhead[i,j] for outgoing arcs)=sum(service[j,i]+deadhead[j,i] for incoming arcs) for every i in N"],"objective":"minimize sum(service_costs[{i,j}]*service[i,j]+distance_matrix[i,j]*deadhead[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    dimensions = (0, 1)
    required_edges = (
        (0, 3),
        (0, 4),
        (1, 4),
        (2, 3),
        (2, 5),
        (3, 4),
        (4, 5),
    )

    # Travel is restricted to the seven explicitly allowable street segments.
    arcs = tuple(
        directed_edge
        for first, second in required_edges
        for directed_edge in ((first, second), (second, first))
    )

    coordinates_input = params["coordinates"]
    service_costs_input = params["service_costs"]
    distances_input = params["distance_matrix"]

    if len(coordinates_input) != len(nodes):
        raise ValueError("coordinates must contain six coordinate pairs.")
    if any(
        len(coordinates_input[node]) != len(dimensions)
        for node in nodes
    ):
        raise ValueError("Each coordinate must have two components.")
    if len(service_costs_input) != len(required_edges):
        raise ValueError("service_costs must contain seven entries.")

    coordinate_data = {
        (node, dimension): coordinates_input[node][dimension]
        for node in nodes
        for dimension in dimensions
    }
    service_cost_data = {
        edge: service_costs_input[position]
        for position, edge in enumerate(required_edges)
    }

    upper_pairs = tuple(
        (first, second)
        for first in nodes
        for second in nodes
        if first < second
    )

    if len(distances_input) == len(nodes):
        if any(
            len(distances_input[node]) != len(nodes)
            for node in nodes
        ):
            raise ValueError("distance_matrix must be a 6x6 matrix.")
        distance_data = {
            (first, second): distances_input[first][second]
            for first in nodes
            for second in nodes
        }
    elif len(distances_input) == len(upper_pairs):
        distance_data = {(node, node): 0 for node in nodes}
        for position, (first, second) in enumerate(upper_pairs):
            value = distances_input[position]
            distance_data[first, second] = value
            distance_data[second, first] = value
    else:
        raise ValueError(
            "distance_matrix must contain six rows or "
            "15 upper-triangular entries."
        )

    outgoing = {
        node: tuple(second for first, second in arcs if first == node)
        for node in nodes
    }
    incoming = {
        node: tuple(first for first, second in arcs if second == node)
        for node in nodes
    }
    arc_service_cost = {
        (first, second): service_cost_data[
            (first, second) if first < second else (second, first)
        ]
        for first, second in arcs
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.D = pyo.Set(initialize=dimensions, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=required_edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.coordinates = pyo.Param(
        model.N,
        model.D,
        initialize=coordinate_data,
        within=pyo.Reals,
    )
    model.service_costs = pyo.Param(
        model.E,
        initialize=service_cost_data,
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.N,
        model.N,
        initialize=distance_data,
        within=pyo.NonNegativeReals,
    )

    model.service = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.deadhead = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)

    def service_coverage_rule(instance, first, second):
        return (
            instance.service[first, second]
            + instance.service[second, first]
            >= 1
        )

    model.service_coverage = pyo.Constraint(
        model.E, rule=service_coverage_rule
    )

    def flow_balance_rule(instance, node):
        return sum(
            instance.service[node, neighbor]
            + instance.deadhead[node, neighbor]
            for neighbor in outgoing[node]
        ) == sum(
            instance.service[neighbor, node]
            + instance.deadhead[neighbor, node]
            for neighbor in incoming[node]
        )

    model.flow_balance = pyo.Constraint(
        model.N, rule=flow_balance_rule
    )

    # Required edges connect all six nodes, including depot 0. Their mandatory
    # coverage therefore makes the balanced traversal support connected,
    # admitting a single Euler tour that starts and ends at depot 0.
    model.total_cost = pyo.Objective(
        expr=sum(
            arc_service_cost[first, second]
            * model.service[first, second]
            + model.distance_matrix[first, second]
            * model.deadhead[first, second]
            for first, second in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow the objective retrieval below to determine success when
        # automatic solution loading reports that no solution is available.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}