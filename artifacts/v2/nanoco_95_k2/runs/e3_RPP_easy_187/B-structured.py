# IR: {
#   "sets": {"N": "range(num_nodes)", "A": "all (i,j) in N*N with i != j", "R": "required_edges", "T": "endpoints of R excluding depot_node"},
#   "params": {"distance_matrix": "nonnegative row-major direct costs", "required_edges": "undirected mandatory node pairs", "depot_node": "route origin and destination", "num_nodes": "node count", "num_required_edges": "required-edge count", "K": "|T|"},
#   "variables": {"x[i,j]": "nonnegative integer traversal count on A", "f[i,j]": "nonnegative continuous connectivity flow on A"},
#   "constraints": [
#     "Service: x[u,v] + x[v,u] >= 1 for every (u,v) in R.",
#     "Route balance: sum_j x[i,j] = sum_j x[j,i] for every i in N.",
#     "Flow capacity: f[i,j] <= K*x[i,j] for every (i,j) in A.",
#     "Connectivity: outgoing f minus incoming f equals K at the depot, -1 at each node in T, and 0 elsewhere."
#   ],
#   "objective": "minimize sum_(i,j in A) distance_matrix[i*num_nodes+j]*x[i,j]"
# }

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_count_raw = params["num_nodes"]
    required_count_raw = params["num_required_edges"]
    distance_data = params["distance_matrix"]
    required_data = params["required_edges"]
    depot_raw = params["depot_node"]

    node_count = int(node_count_raw)
    required_count = int(required_count_raw)
    depot = int(depot_raw)

    if (
        node_count != node_count_raw
        or required_count != required_count_raw
        or depot != depot_raw
        or node_count < 1
        or required_count < 0
        or not 0 <= depot < node_count
    ):
        return {"objective": None, "status": "invalid_parameters"}

    if (
        len(distance_data) != node_count * node_count
        or len(required_data) != required_count
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    distances = [float(value) for value in distance_data]
    if any(not math.isfinite(value) or value < 0 for value in distances):
        return {"objective": None, "status": "invalid_costs"}

    required_pairs = []
    for pair in required_data:
        if len(pair) != 2:
            return {"objective": None, "status": "invalid_required_edge"}

        first = int(pair[0])
        second = int(pair[1])
        if (
            first != pair[0]
            or second != pair[1]
            or not 0 <= first < node_count
            or not 0 <= second < node_count
            or first == second
        ):
            return {"objective": None, "status": "invalid_required_edge"}

        required_pairs.append((first, second))

    nodes = list(range(node_count))
    arcs = [(first, second) for first in nodes for second in nodes
            if first != second]
    terminals = sorted(
        {endpoint for pair in required_pairs for endpoint in pair} - {depot}
    )
    terminal_set = set(terminals)
    flow_units = len(terminals)

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.R = pyo.Set(dimen=2, initialize=required_pairs, ordered=True)
    model.T = pyo.Set(initialize=terminals, ordered=True)

    model.travel_cost = pyo.Param(
        model.A,
        initialize={
            (first, second): distances[first * node_count + second]
            for first, second in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.K = pyo.Param(initialize=flow_units, within=pyo.NonNegativeIntegers)

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def service_rule(network, first, second):
        return network.x[first, second] + network.x[second, first] >= 1

    model.service_requirement = pyo.Constraint(model.R, rule=service_rule)

    def route_balance_rule(network, node):
        if node_count == 1:
            return pyo.Constraint.Feasible
        return (
            sum(network.x[node, other] for other in nodes if other != node)
            == sum(network.x[other, node] for other in nodes if other != node)
        )

    model.route_balance = pyo.Constraint(model.N, rule=route_balance_rule)

    def capacity_rule(network, first, second):
        return network.f[first, second] <= network.K * network.x[first, second]

    model.connectivity_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    def connectivity_rule(network, node):
        if node_count == 1:
            return pyo.Constraint.Feasible

        if node == depot:
            net_supply = flow_units
        elif node in terminal_set:
            net_supply = -1
        else:
            net_supply = 0

        return (
            sum(network.f[node, other] for other in nodes if other != node)
            - sum(network.f[other, node] for other in nodes if other != node)
            == net_supply
        )

    model.connectivity_balance = pyo.Constraint(
        model.N, rule=connectivity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[first, second] * model.x[first, second]
            for first, second in arcs
        ),
        sense=pyo.minimize,
    )

    # Catch only the expected APPSI failure to load a feasible solution.
    # Unexpected solver exceptions propagate to the calling harness.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrieval is the sole success test.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}