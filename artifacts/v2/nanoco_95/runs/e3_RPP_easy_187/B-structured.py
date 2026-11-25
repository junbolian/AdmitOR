# IR: {"sets":{"V":"range(params['num_nodes'])","A":"{(i,j): i,j in V, i != j}","P":[[0,6],[0,7],[1,2],[1,3],[2,7],[4,6],[4,7],[4,8],[5,6],[5,8]],"R":[[0,6],[0,7],[1,3],[2,7],[4,7],[4,8],[5,6],[5,8]]},"params":{"distance_matrix":"nonnegative direct traversal costs","depot_coordinates":"frozen metadata","node_coordinates":"frozen metadata","num_nodes":"frozen cardinality, 9","num_physical_edges":"frozen cardinality, |P|","num_required_edges":"frozen cardinality, |R|","required_edge_ratio":"metadata; does not restrict travel"},"variables":{"x[i,j]":"nonnegative integer traversal count, (i,j) in A","f[i,j]":"nonnegative continuous connectivity flow, (i,j) in A"},"constraints":["x[i,j]+x[j,i]>=1 for (i,j) in R","sum_j x[v,j]=sum_i x[i,v] for v in V","sum_j f[0,j]-sum_i f[i,0]=|V|-1","sum_i f[i,v]-sum_j f[v,j]=1 for v in V excluding 0","f[i,j]<=(|V|-1)*x[i,j] for (i,j) in A"],"objective":"minimize sum_(i,j in A) distance_matrix[i][j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    depot_coordinates = params["depot_coordinates"]
    node_coordinates = params["node_coordinates"]
    num_nodes = params["num_nodes"]
    num_physical_edges = params["num_physical_edges"]
    num_required_edges = params["num_required_edges"]
    required_edge_ratio = params["required_edge_ratio"]

    # Coordinates and the required-edge ratio describe the frozen instance;
    # routing costs come exclusively from distance_matrix.
    metadata = {
        "depot_coordinates": depot_coordinates,
        "node_coordinates": node_coordinates,
        "required_edge_ratio": required_edge_ratio,
    }

    physical_edges = (
        (0, 6), (0, 7), (1, 2), (1, 3), (2, 7),
        (4, 6), (4, 7), (4, 8), (5, 6), (5, 8),
    )
    required_edges = (
        (0, 6), (0, 7), (1, 3), (2, 7),
        (4, 7), (4, 8), (5, 6), (5, 8),
    )

    if (
        num_nodes != 9
        or num_physical_edges != len(physical_edges)
        or num_required_edges != len(required_edges)
    ):
        return {"objective": None, "status": "invalid_cardinality"}

    if (
        len(distance_matrix) != num_nodes
        or any(len(row) != num_nodes for row in distance_matrix)
    ):
        return {"objective": None, "status": "invalid_matrix_shape"}

    vertices = tuple(range(num_nodes))
    arcs = tuple(
        (source, target)
        for source in vertices
        for target in vertices
        if source != target
    )

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.R = pyo.Set(dimen=2, initialize=required_edges, ordered=True)

    model.travel_cost = pyo.Param(
        model.A,
        initialize={
            (source, target): distance_matrix[source][target]
            for source, target in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.x = pyo.Var(model.A, domain=pyo.NonNegativeIntegers)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def service_rule(network, source, target):
        return network.x[source, target] + network.x[target, source] >= 1

    model.required_service = pyo.Constraint(model.R, rule=service_rule)

    def balance_rule(network, vertex):
        return sum(
            network.x[vertex, other]
            for other in vertices
            if other != vertex
        ) == sum(
            network.x[other, vertex]
            for other in vertices
            if other != vertex
        )

    model.traversal_balance = pyo.Constraint(model.V, rule=balance_rule)

    # Every junction is incident to a required edge in this frozen instance.
    # Sending one unit to each nondepot junction eliminates disconnected tours.
    def connectivity_rule(network, vertex):
        outgoing = sum(
            network.f[vertex, other]
            for other in vertices
            if other != vertex
        )
        incoming = sum(
            network.f[other, vertex]
            for other in vertices
            if other != vertex
        )
        if vertex == 0:
            return outgoing - incoming == num_nodes - 1
        return incoming - outgoing == 1

    model.connectivity_balance = pyo.Constraint(
        model.V, rule=connectivity_rule
    )

    def capacity_rule(network, source, target):
        return (
            network.f[source, target]
            <= (num_nodes - 1) * network.x[source, target]
        )

    model.connectivity_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[source, target] * model.x[source, target]
            for source, target in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}