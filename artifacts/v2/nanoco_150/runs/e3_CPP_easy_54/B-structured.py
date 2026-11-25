# IR: {"sets":{"V":"0..7","E":"[(0,1),(0,3),(0,6),(1,3),(1,5),(1,6),(2,3),(2,4),(5,7)]","S":"both orientations of E","A":"all ordered distinct node pairs","K":"[0,1]"},"params":{"c":"params['edge_costs'], ordered scalar costs or [u,v,cost] records","d":"params['distance_matrix']","q":"params['coords']","length":"Euclidean endpoint distance for each E; geometry only","depot":0,"F":"|V|-1"},"variables":{"service[S]":"nonnegative integer service traversals","transit[A]":"nonnegative integer deadheading traversals","flow[A]":"nonnegative continuous connectivity flow"},"expressions":{"traversals[i,j]":"transit[i,j]+service[i,j] if (i,j) in S, otherwise transit[i,j]"},"constraints":["service[u,v]+service[v,u]>=1 for each (u,v) in E","sum_j traversals[i,j]=sum_j traversals[j,i] for each i in V","flow[i,j]<=F*traversals[i,j] for each (i,j) in A","sum_j flow[i,j]-sum_j flow[j,i]=F if i=depot, otherwise -1"],"objective":"minimize sum_(i,j in S) c[{i,j}]*service[i,j]+sum_(i,j in A) d[i,j]*transit[i,j]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    depot = 0
    graph_edges = (
        (0, 1),
        (0, 3),
        (0, 6),
        (1, 3),
        (1, 5),
        (1, 6),
        (2, 3),
        (2, 4),
        (5, 7),
    )
    service_arcs = tuple(
        arc
        for start, end in graph_edges
        for arc in ((start, end), (end, start))
    )
    transit_arcs = tuple(
        (start, end)
        for start in nodes
        for end in nodes
        if start != end
    )
    service_arc_set = set(service_arcs)

    raw_edge_costs = params["edge_costs"]
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]

    if len(raw_edge_costs) != len(graph_edges):
        raise ValueError("edge_costs must contain one entry per required edge.")
    if len(distance_matrix) != len(nodes) or any(
        len(row) != len(nodes) for row in distance_matrix
    ):
        raise ValueError("distance_matrix must be an 8 by 8 matrix.")
    if len(coords) != len(nodes) or any(len(point) != 2 for point in coords):
        raise ValueError("coords must contain eight two-dimensional points.")

    service_costs = {}
    for edge_index, (start, end) in enumerate(graph_edges):
        entry = raw_edge_costs[edge_index]
        if isinstance(entry, (list, tuple)):
            if len(entry) != 3:
                raise ValueError("Each edge-cost record must be [u, v, cost].")
            record_start, record_end, cost = entry
            if (record_start, record_end) not in (
                (start, end),
                (end, start),
            ):
                raise ValueError("edge_costs records must follow the listed order.")
        else:
            cost = entry

        service_costs[start, end] = float(cost)
        service_costs[end, start] = float(cost)

    transit_costs = {
        (start, end): float(distance_matrix[start][end])
        for start, end in transit_arcs
    }
    coordinate_values = {
        (node, axis): float(coords[node][axis])
        for node in nodes
        for axis in range(2)
    }

    if any(
        not math.isfinite(cost) or cost < 0
        for cost in (*service_costs.values(), *transit_costs.values())
    ):
        raise ValueError("Travel costs must be finite and nonnegative.")
    if any(not math.isfinite(value) for value in coordinate_values.values()):
        raise ValueError("Coordinates must be finite.")

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=graph_edges, ordered=True)
    model.S = pyo.Set(dimen=2, initialize=service_arcs, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=transit_arcs, ordered=True)
    model.K = pyo.Set(initialize=(0, 1), ordered=True)

    model.depot = pyo.Param(initialize=depot, within=pyo.NonNegativeIntegers)
    model.F = pyo.Param(
        initialize=len(nodes) - 1, within=pyo.NonNegativeIntegers
    )
    model.c = pyo.Param(
        model.S, initialize=service_costs, within=pyo.NonNegativeReals
    )
    model.d = pyo.Param(
        model.A, initialize=transit_costs, within=pyo.NonNegativeReals
    )
    model.q = pyo.Param(
        model.V, model.K, initialize=coordinate_values, within=pyo.Reals
    )

    def length_rule(instance, start, end):
        return math.hypot(
            pyo.value(instance.q[start, 0] - instance.q[end, 0]),
            pyo.value(instance.q[start, 1] - instance.q[end, 1]),
        )

    # Retain geometric lengths independently of the supplied travel costs.
    model.length = pyo.Param(
        model.E, initialize=length_rule, within=pyo.NonNegativeReals
    )

    model.service = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.transit = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def traversals_rule(instance, start, end):
        if (start, end) in service_arc_set:
            return instance.transit[start, end] + instance.service[start, end]
        return instance.transit[start, end]

    model.traversals = pyo.Expression(model.A, rule=traversals_rule)

    def coverage_rule(instance, start, end):
        return instance.service[start, end] + instance.service[end, start] >= 1

    model.coverage = pyo.Constraint(model.E, rule=coverage_rule)

    def balance_rule(instance, node):
        return sum(
            instance.traversals[node, other]
            for other in instance.V
            if other != node
        ) == sum(
            instance.traversals[other, node]
            for other in instance.V
            if other != node
        )

    model.balance = pyo.Constraint(model.V, rule=balance_rule)

    def flow_capacity_rule(instance, start, end):
        return (
            instance.flow[start, end]
            <= instance.F * instance.traversals[start, end]
        )

    model.flow_capacity = pyo.Constraint(model.A, rule=flow_capacity_rule)

    def connectivity_rule(instance, node):
        outgoing = sum(
            instance.flow[node, other]
            for other in instance.V
            if other != node
        )
        incoming = sum(
            instance.flow[other, node]
            for other in instance.V
            if other != node
        )
        supply = instance.F if node == pyo.value(instance.depot) else -1
        return outgoing - incoming == supply

    model.connectivity = pyo.Constraint(model.V, rule=connectivity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.c[start, end] * model.service[start, end]
            for start, end in model.S
        )
        + sum(
            model.d[start, end] * model.transit[start, end]
            for start, end in model.A
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}