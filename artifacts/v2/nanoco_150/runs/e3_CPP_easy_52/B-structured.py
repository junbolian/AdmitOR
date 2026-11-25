# IR: {"sets":{"N":"range(num_nodes)","A":"ordered pairs of distinct nodes","G":"undirected graph_edges","R":"undirected required_edges","S":"both orientations of R","T":"endpoints of R excluding depot"},"params":{"num_nodes":"params[num_nodes]","depot":"params[depot]","coords":"params[coords], coordinate metadata","distance_matrix":"params[distance_matrix], transit costs","num_graph_edges":"params[num_graph_edges]","graph_edges":"params[graph_edges], designated streets","num_required_edges":"params[num_required_edges]","required_edges":"params[required_edges], required streets","edge_costs":"params[edge_costs], service costs"},"derived":{"Q":"cardinality(T)"},"variables":{"transit[A]":"nonnegative integer, direct transit traversals","service[S]":"nonnegative integer, service traversals","commodity[A]":"nonnegative continuous, depot connectivity flow"},"expressions":{"traversals[i,j]":"transit[i,j] + service[i,j] when (i,j) is in S, otherwise transit[i,j]"},"constraints":["service[u,v] + service[v,u] >= 1 for each {u,v} in R","sum_j traversals[i,j] - sum_j traversals[j,i] = 0 for each i in N","commodity[i,j] <= Q * traversals[i,j] for each (i,j) in A","sum_j commodity[i,j] - sum_j commodity[j,i] = Q at depot, -1 at nodes in T, and 0 elsewhere"],"objective":"minimize sum_(i,j in A) distance_matrix[i][j]*transit[i,j] + sum_(i,j in S) service_cost[{i,j}]*service[i,j]","assumptions":["Costs are finite and nonnegative.","Service and transit are separate traversal modes; each traversal pays its selected mode's cost.","Connectivity flow connects every required street to the depot; any disconnected transit-only cycles can be removed without increasing cost, so an optimal closed route exists with the model's objective."]}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    depot = params["depot"]
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]
    num_graph_edges = params["num_graph_edges"]
    graph_edges = params["graph_edges"]
    num_required_edges = params["num_required_edges"]
    required_edges = params["required_edges"]
    edge_costs = params["edge_costs"]

    if not isinstance(num_nodes, int) or isinstance(num_nodes, bool) or num_nodes < 1:
        raise ValueError("num_nodes must be a positive integer.")

    nodes = list(range(num_nodes))

    def validate_node(node):
        if (
            not isinstance(node, int)
            or isinstance(node, bool)
            or node < 0
            or node >= num_nodes
        ):
            raise ValueError("Every node index must belong to range(num_nodes).")

    validate_node(depot)

    if len(coords) != num_nodes or any(len(point) != 2 for point in coords):
        raise ValueError("coords must contain one coordinate pair per node.")
    if any(not math.isfinite(float(value)) for point in coords for value in point):
        raise ValueError("Coordinates must be finite.")

    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix must be square and match num_nodes.")

    transit_cost = {}
    for source in nodes:
        for target in nodes:
            value = float(distance_matrix[source][target])
            if not math.isfinite(value) or value < 0:
                raise ValueError("Transit costs must be finite and nonnegative.")
            if source != target:
                transit_cost[source, target] = value

    if num_graph_edges != len(graph_edges):
        raise ValueError("num_graph_edges does not match graph_edges.")
    if num_required_edges != len(required_edges):
        raise ValueError("num_required_edges does not match required_edges.")

    def normalize_edge(edge):
        if len(edge) != 2:
            raise ValueError("Each street must contain exactly two node indices.")
        source, target = edge
        validate_node(source)
        validate_node(target)
        if source == target:
            raise ValueError("Street endpoints must be distinct.")
        return (min(source, target), max(source, target))

    designated_edges = [normalize_edge(edge) for edge in graph_edges]
    required_streets = [normalize_edge(edge) for edge in required_edges]

    if len(set(designated_edges)) != len(designated_edges):
        raise ValueError("graph_edges contains duplicate undirected streets.")
    if len(set(required_streets)) != len(required_streets):
        raise ValueError("required_edges contains duplicate undirected streets.")
    if not set(required_streets).issubset(set(designated_edges)):
        raise ValueError("Every required street must belong to graph_edges.")

    service_cost = {}
    for entry in edge_costs:
        if len(entry) != 3:
            raise ValueError("Each edge_costs entry must contain [u, v, cost].")
        edge = normalize_edge(entry[:2])
        value = float(entry[2])
        if not math.isfinite(value) or value < 0:
            raise ValueError("Service costs must be finite and nonnegative.")
        if edge in service_cost and service_cost[edge] != value:
            raise ValueError("Conflicting service costs for an undirected street.")
        service_cost[edge] = value

    if any(edge not in service_cost for edge in required_streets):
        raise ValueError("Every required street must have a service cost.")

    arcs = [
        (source, target)
        for source in nodes
        for target in nodes
        if source != target
    ]
    service_arcs = [
        arc
        for source, target in required_streets
        for arc in ((source, target), (target, source))
    ]
    service_arc_set = set(service_arcs)
    terminals = {
        node
        for edge in required_streets
        for node in edge
        if node != depot
    }
    connectivity_demand = len(terminals)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.transit_arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.required_streets = pyo.Set(
        dimen=2, initialize=required_streets, ordered=True
    )
    model.service_arcs = pyo.Set(
        dimen=2, initialize=service_arcs, ordered=True
    )

    model.transit = pyo.Var(
        model.transit_arcs, domain=pyo.NonNegativeIntegers
    )
    model.service = pyo.Var(
        model.service_arcs, domain=pyo.NonNegativeIntegers
    )
    model.commodity = pyo.Var(
        model.transit_arcs, domain=pyo.NonNegativeReals
    )

    def traversal_rule(block, source, target):
        if (source, target) in service_arc_set:
            return block.transit[source, target] + block.service[source, target]
        return block.transit[source, target]

    model.traversals = pyo.Expression(
        model.transit_arcs, rule=traversal_rule
    )

    def coverage_rule(block, source, target):
        return block.service[source, target] + block.service[target, source] >= 1

    model.service_coverage = pyo.Constraint(
        model.required_streets, rule=coverage_rule
    )

    def route_balance_rule(block, node):
        if num_nodes == 1:
            return pyo.Constraint.Skip
        return (
            pyo.quicksum(
                block.traversals[node, other]
                for other in nodes
                if other != node
            )
            - pyo.quicksum(
                block.traversals[other, node]
                for other in nodes
                if other != node
            )
            == 0
        )

    model.route_balance = pyo.Constraint(
        model.nodes, rule=route_balance_rule
    )

    def capacity_rule(block, source, target):
        return (
            block.commodity[source, target]
            <= connectivity_demand * block.traversals[source, target]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.transit_arcs, rule=capacity_rule
    )

    def connectivity_balance_rule(block, node):
        if num_nodes == 1:
            return pyo.Constraint.Skip
        if node == depot:
            net_supply = connectivity_demand
        elif node in terminals:
            net_supply = -1
        else:
            net_supply = 0
        return (
            pyo.quicksum(
                block.commodity[node, other]
                for other in nodes
                if other != node
            )
            - pyo.quicksum(
                block.commodity[other, node]
                for other in nodes
                if other != node
            )
            == net_supply
        )

    model.connectivity_balance = pyo.Constraint(
        model.nodes, rule=connectivity_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                transit_cost[source, target] * model.transit[source, target]
                for source, target in arcs
            )
            + pyo.quicksum(
                service_cost[min(source, target), max(source, target)]
                * model.service[source, target]
                for source, target in service_arcs
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}