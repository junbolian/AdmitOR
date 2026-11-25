# IR: {"sets":{"V":[0,1,2,3,4,5,6,7,8],"A":"all ordered pairs (i,j) in V x V with i != j","R":[[0,3],[1,7],[2,8],[3,7],[4,5],[4,6],[5,7],[5,8]]},"params":{"distance_inputs":["dist_0_1","dist_0_2","dist_0_3","dist_0_4","dist_0_5","dist_0_6","dist_0_7","dist_0_8","dist_1_2","dist_1_3","dist_1_4","dist_1_5","dist_1_6","dist_1_7","dist_1_8","dist_2_3","dist_2_4_asym","dist_2_5","dist_2_6","dist_2_7","dist_2_8","dist_3_4","dist_3_5","dist_3_6","dist_3_7","dist_3_8","dist_4_2_asym","dist_4_5","dist_4_6","dist_4_7","dist_4_8","dist_5_6","dist_5_7","dist_5_8","dist_6_7","dist_6_8","dist_7_8"],"c[i,j]":"distance_inputs mapped by endpoints; reverse costs equal forward costs except c[4,2] uses dist_4_2_asym","K":"|V|-1"},"variables":{"x[i,j]":"nonnegative integer traversal count for (i,j) in A","f[i,j]":"nonnegative continuous connectivity flow for (i,j) in A"},"constraints":["sum_j x[i,j] = sum_j x[j,i] for every i in V","x[i,j] + x[j,i] >= 1 for every (i,j) in R","sum_j f[0,j] - sum_j f[j,0] = K","sum_j f[j,i] - sum_j f[i,j] = 1 for every i in V except 0","f[i,j] <= K*x[i,j] for every (i,j) in A"],"objective":"minimize sum_(i,j in A) c[i,j]*x[i,j]","route_recovery":"Hierholzer traversal from depot 0 using integer arc multiplicities; retained internally because the required return schema contains only objective and status"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    upper_distances = {
        (0, 1): params["dist_0_1"],
        (0, 2): params["dist_0_2"],
        (0, 3): params["dist_0_3"],
        (0, 4): params["dist_0_4"],
        (0, 5): params["dist_0_5"],
        (0, 6): params["dist_0_6"],
        (0, 7): params["dist_0_7"],
        (0, 8): params["dist_0_8"],
        (1, 2): params["dist_1_2"],
        (1, 3): params["dist_1_3"],
        (1, 4): params["dist_1_4"],
        (1, 5): params["dist_1_5"],
        (1, 6): params["dist_1_6"],
        (1, 7): params["dist_1_7"],
        (1, 8): params["dist_1_8"],
        (2, 3): params["dist_2_3"],
        (2, 4): params["dist_2_4_asym"],
        (2, 5): params["dist_2_5"],
        (2, 6): params["dist_2_6"],
        (2, 7): params["dist_2_7"],
        (2, 8): params["dist_2_8"],
        (3, 4): params["dist_3_4"],
        (3, 5): params["dist_3_5"],
        (3, 6): params["dist_3_6"],
        (3, 7): params["dist_3_7"],
        (3, 8): params["dist_3_8"],
        (4, 5): params["dist_4_5"],
        (4, 6): params["dist_4_6"],
        (4, 7): params["dist_4_7"],
        (4, 8): params["dist_4_8"],
        (5, 6): params["dist_5_6"],
        (5, 7): params["dist_5_7"],
        (5, 8): params["dist_5_8"],
        (6, 7): params["dist_6_7"],
        (6, 8): params["dist_6_8"],
        (7, 8): params["dist_7_8"],
    }

    distances = {}
    for (source, destination), distance in upper_distances.items():
        distances[source, destination] = distance
        distances[destination, source] = distance
    distances[4, 2] = params["dist_4_2_asym"]

    nodes = tuple(range(9))
    arcs = tuple(
        (source, destination)
        for source in nodes
        for destination in nodes
        if source != destination
    )
    required_edges = (
        (0, 3),
        (1, 7),
        (2, 8),
        (3, 7),
        (4, 5),
        (4, 6),
        (5, 7),
        (5, 8),
    )
    connectivity_demand = len(nodes) - 1

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.travel_cost = pyo.Param(model.arcs, initialize=distances)

    model.traversals = pyo.Var(
        model.arcs, domain=pyo.NonNegativeIntegers
    )
    model.connectivity_flow = pyo.Var(
        model.arcs, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, vertex):
        return (
            sum(
                instance.traversals[vertex, neighbor]
                for neighbor in instance.vertices
                if neighbor != vertex
            )
            == sum(
                instance.traversals[neighbor, vertex]
                for neighbor in instance.vertices
                if neighbor != vertex
            )
        )

    model.traversal_balance = pyo.Constraint(
        model.vertices, rule=balance_rule
    )

    def service_rule(instance, source, destination):
        return (
            instance.traversals[source, destination]
            + instance.traversals[destination, source]
            >= 1
        )

    model.service_coverage = pyo.Constraint(
        model.required_edges, rule=service_rule
    )

    def connectivity_balance_rule(instance, vertex):
        outgoing = sum(
            instance.connectivity_flow[vertex, neighbor]
            for neighbor in instance.vertices
            if neighbor != vertex
        )
        incoming = sum(
            instance.connectivity_flow[neighbor, vertex]
            for neighbor in instance.vertices
            if neighbor != vertex
        )
        if vertex == 0:
            return outgoing - incoming == connectivity_demand
        return incoming - outgoing == 1

    # Every node is incident to a mandatory edge, so every node must
    # belong to the depot-connected route.
    model.connectivity_balance = pyo.Constraint(
        model.vertices, rule=connectivity_balance_rule
    )

    def connectivity_capacity_rule(instance, source, destination):
        return (
            instance.connectivity_flow[source, destination]
            <= connectivity_demand
            * instance.traversals[source, destination]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.arcs, rule=connectivity_capacity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[source, destination]
            * model.traversals[source, destination]
            for source, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # Recover the exact closed walk, including repeated traversals.
    remaining = {
        (source, destination): int(
            round(pyo.value(model.traversals[source, destination]))
        )
        for source, destination in arcs
    }
    successors = {
        source: [
            destination
            for destination in nodes
            if source != destination
            and remaining[source, destination] > 0
        ]
        for source in nodes
    }

    stack = [0]
    reverse_route = []
    while stack:
        source = stack[-1]
        while (
            successors[source]
            and remaining[source, successors[source][-1]] == 0
        ):
            successors[source].pop()

        if successors[source]:
            destination = successors[source][-1]
            remaining[source, destination] -= 1
            stack.append(destination)
        else:
            reverse_route.append(stack.pop())

    optimal_route = list(reversed(reverse_route))
    model.optimal_route = optimal_route

    return {"objective": obj_val, "status": "optimal"}