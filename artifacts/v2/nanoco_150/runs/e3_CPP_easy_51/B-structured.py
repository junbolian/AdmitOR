# IR: {"sets":{"V":"0..num_nodes-1","E":[[0,7],[1,7],[2,5],[2,7],[3,6],[3,7],[4,6],[5,6],[5,7]],"R":"E","A":"both orientations of E","P":"all unordered pairs of distinct nodes"},"params":{"edge_cost":"params[edge_cost_i_j] for E","distance":"params[dist_i_j] for P, symmetric","coordinates":"params[coord_x_i], params[coord_y_i] for V; metadata only","counts":"params[num_nodes], params[num_graph_edges], params[num_required_edges]","depot":"params[depot]"},"validation":["num_nodes=8; num_graph_edges=|E|; num_required_edges=|R|; depot belongs to V"],"variables":{"service[i,j]":"binary for A","deadhead[i,j]":"nonnegative integer for A"},"constraints":["service[i,j]+service[j,i]=1 for each required edge {i,j}","sum_j(service[v,j]+deadhead[v,j])=sum_j(service[j,v]+deadhead[j,v]) for every v, including depot"],"objective":"minimize sum_{(i,j) in A}(edge_cost[{i,j}]*service[i,j]+distance[{i,j}]*deadhead[i,j])","connectivity":"Every edge of the fixed connected graph is required; coverage and balance therefore guarantee one closed Euler route through the depot."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    graph_edges = (
        (0, 7),
        (1, 7),
        (2, 5),
        (2, 7),
        (3, 6),
        (3, 7),
        (4, 6),
        (5, 6),
        (5, 7),
    )

    num_nodes = params["num_nodes"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    depot = params["depot"]

    if (
        num_nodes != 8
        or num_graph_edges != len(graph_edges)
        or num_required_edges != len(graph_edges)
        or depot not in range(8)
    ):
        return {"objective": None, "status": "invalid_structure"}

    nodes = tuple(range(8))
    pairs = tuple(
        (first, second)
        for first in nodes
        for second in nodes
        if first < second
    )
    arcs = tuple(
        directed_edge
        for first, second in graph_edges
        for directed_edge in ((first, second), (second, first))
    )

    edge_costs = {
        (first, second): params[f"edge_cost_{first}_{second}"]
        for first, second in graph_edges
    }
    distances = {
        (first, second): params[f"dist_{first}_{second}"]
        for first, second in pairs
    }
    coordinates_x = {
        vertex: params[f"coord_x_{vertex}"] for vertex in nodes
    }
    coordinates_y = {
        vertex: params[f"coord_y_{vertex}"] for vertex in nodes
    }
    neighbors = {
        vertex: tuple(
            second for first, second in arcs if first == vertex
        )
        for vertex in nodes
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=graph_edges, ordered=True)
    model.R = pyo.Set(dimen=2, initialize=graph_edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.P = pyo.Set(dimen=2, initialize=pairs, ordered=True)

    model.node_count = pyo.Param(
        initialize=num_nodes, within=pyo.PositiveIntegers
    )
    model.graph_edge_count = pyo.Param(
        initialize=num_graph_edges, within=pyo.NonNegativeIntegers
    )
    model.required_edge_count = pyo.Param(
        initialize=num_required_edges, within=pyo.NonNegativeIntegers
    )
    model.depot_node = pyo.Param(initialize=depot, within=model.V)
    model.service_cost = pyo.Param(
        model.E, initialize=edge_costs, within=pyo.NonNegativeReals
    )
    model.travel_distance = pyo.Param(
        model.P, initialize=distances, within=pyo.NonNegativeReals
    )
    model.coordinate_x = pyo.Param(
        model.V, initialize=coordinates_x, within=pyo.Reals
    )
    model.coordinate_y = pyo.Param(
        model.V, initialize=coordinates_y, within=pyo.Reals
    )

    # A service traversal treats an edge once. Any additional traversal is
    # deadheading. Variables exist only on physical road segments.
    model.service = pyo.Var(model.A, domain=pyo.Binary)
    model.deadhead = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)

    def coverage_rule(instance, first, second):
        return (
            instance.service[first, second]
            + instance.service[second, first]
            == 1
        )

    model.service_coverage = pyo.Constraint(
        model.R, rule=coverage_rule
    )

    def balance_rule(instance, vertex):
        return sum(
            instance.service[vertex, neighbor]
            + instance.deadhead[vertex, neighbor]
            for neighbor in neighbors[vertex]
        ) == sum(
            instance.service[neighbor, vertex]
            + instance.deadhead[neighbor, vertex]
            for neighbor in neighbors[vertex]
        )

    model.flow_balance = pyo.Constraint(model.V, rule=balance_rule)

    # All physical edges are required and their graph is connected.
    # Coverage thus supplies connectivity, and balance supplies an Euler
    # circuit that can start and end at the designated depot.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.service_cost[
                min(first, second), max(first, second)
            ]
            * model.service[first, second]
            + model.travel_distance[
                min(first, second), max(first, second)
            ]
            * model.deadhead[first, second]
            for first, second in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi can raise this when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}