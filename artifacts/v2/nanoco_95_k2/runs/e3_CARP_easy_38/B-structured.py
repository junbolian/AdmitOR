# IR: {"sets":{"N":"range(params['num_nodes'])","K":"range(params['num_vehicles'])","S":"[(0,3),(0,4),(2,3),(3,4)] in demand order","O":[0,1],"A":"{(i,j) in N x N: i != j}","N_plus":"N excluding depot 0"},"params":{"vehicle_capacity":"params['vehicle_capacity']","demands":"params['demands']","num_vehicles":"params['num_vehicles']","num_service_segments":"params['num_service_segments']","num_nodes":"params['num_nodes']","distance_matrix":"params['distance_matrix']","node_coordinates":"params['node_coordinates']","B":"num_service_segments+(num_service_segments+1)*(num_nodes-1)"},"variables":{"travel[k,i,j]":"nonnegative integer traversal count on A","service[k,s,o]":"binary; orientation 0 follows S[s], orientation 1 reverses it","visited[k,i]":"binary for i in N_plus","connectivity[k,i,j]":"nonnegative continuous flow on A"},"constraints":["sum(k,o) service[k,s,o] = 1 for each s","sum(s,o) demands[s]*service[k,s,o] <= vehicle_capacity for each k","sum(s,o) service[k,s,o] >= 1 for each k","travel[k,oriented_start(s,o),oriented_end(s,o)] >= service[k,s,o]","sum(j!=i) travel[k,i,j] = sum(j!=i) travel[k,j,i] for each k,i","sum(j!=0) travel[k,0,j] >= 1 for each k","visited[k,i] <= sum(j!=i) travel[k,i,j] <= B*visited[k,i] for each k,i in N_plus","sum((i,j) in A) travel[k,i,j] <= B for each k","connectivity[k,i,j] <= (num_nodes-1)*travel[k,i,j] for each k,(i,j) in A","sum(j!=i) connectivity[k,j,i]-sum(j!=i) connectivity[k,i,j] = visited[k,i] for each k,i in N_plus","sum(j!=0) connectivity[k,0,j]-sum(j!=0) connectivity[k,j,0] = sum(i in N_plus) visited[k,i] for each k"],"objective":"minimize sum(k,(i,j) in A) distance_matrix[i][j]*travel[k,i,j]"}
import math
from numbers import Integral

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vehicle_capacity = params["vehicle_capacity"]
    demands = params["demands"]
    num_vehicles = params["num_vehicles"]
    num_service_segments = params["num_service_segments"]
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    required_segments = ((0, 3), (0, 4), (2, 3), (3, 4))

    counts = (num_vehicles, num_service_segments, num_nodes)
    if any(
        isinstance(count, bool)
        or not isinstance(count, Integral)
        or count <= 0
        for count in counts
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if num_service_segments != len(required_segments):
        return {"objective": None, "status": "invalid_service_count"}

    if any(
        endpoint >= num_nodes
        for segment in required_segments
        for endpoint in segment
    ):
        return {"objective": None, "status": "invalid_node_count"}

    if len(demands) != num_service_segments:
        return {"objective": None, "status": "invalid_demands"}

    if (
        len(distance_matrix) != num_nodes
        or any(len(row) != num_nodes for row in distance_matrix)
        or len(node_coordinates) != num_nodes
        or any(len(point) != 2 for point in node_coordinates)
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if not math.isfinite(vehicle_capacity) or vehicle_capacity < 0:
        return {"objective": None, "status": "invalid_capacity"}

    if any(not math.isfinite(value) or value < 0 for value in demands):
        return {"objective": None, "status": "invalid_demands"}

    if any(
        not math.isfinite(value) or value < 0
        for row in distance_matrix
        for value in row
    ):
        return {"objective": None, "status": "invalid_distances"}

    if any(
        not math.isfinite(value)
        for point in node_coordinates
        for value in point
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    nodes = tuple(range(num_nodes))
    nondepot_nodes = tuple(node for node in nodes if node != 0)
    vehicles = tuple(range(num_vehicles))
    services = tuple(range(num_service_segments))
    orientations = (0, 1)
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    oriented_endpoints = {
        (segment_index, orientation): (
            required_segments[segment_index]
            if orientation == 0
            else required_segments[segment_index][::-1]
        )
        for segment_index in services
        for orientation in orientations
    }

    # Between successive services, nonnegative travel costs allow a simple
    # deadheading path with at most num_nodes - 1 arcs. Thus this bound
    # preserves at least one optimal solution, including nonmetric distances.
    traversal_bound = (
        num_service_segments
        + (num_service_segments + 1) * (num_nodes - 1)
    )

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.N_plus = pyo.Set(initialize=nondepot_nodes, ordered=True)
    model.K = pyo.Set(initialize=vehicles, ordered=True)
    model.S = pyo.Set(initialize=services, ordered=True)
    model.O = pyo.Set(initialize=orientations, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.coordinate_axes = pyo.Set(initialize=("x", "y"), ordered=True)

    model.capacity = pyo.Param(
        initialize=vehicle_capacity, within=pyo.NonNegativeReals
    )
    model.workload = pyo.Param(
        model.S,
        initialize={segment_index: demands[segment_index]
                    for segment_index in services},
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.N,
        model.N,
        initialize={
            (origin, destination): distance_matrix[origin][destination]
            for origin in nodes
            for destination in nodes
        },
        within=pyo.NonNegativeReals,
    )
    # Coordinates are input metadata; the supplied matrix defines all costs.
    model.coordinates = pyo.Param(
        model.N,
        model.coordinate_axes,
        initialize={
            (node, axis): node_coordinates[node][axis_index]
            for node in nodes
            for axis_index, axis in enumerate(("x", "y"))
        },
        within=pyo.Reals,
    )
    model.traversal_limit = pyo.Param(initialize=traversal_bound)
    model.connectivity_limit = pyo.Param(initialize=num_nodes - 1)

    # Travel counts include both service and deadheading traversals.
    model.travel = pyo.Var(
        model.K, model.A, domain=pyo.NonNegativeIntegers
    )
    model.service = pyo.Var(
        model.K, model.S, model.O, domain=pyo.Binary
    )
    model.visited = pyo.Var(
        model.K, model.N_plus, domain=pyo.Binary
    )
    model.connectivity = pyo.Var(
        model.K, model.A, domain=pyo.NonNegativeReals
    )

    def service_once_rule(mdl, segment_index):
        return sum(
            mdl.service[vehicle, segment_index, orientation]
            for vehicle in mdl.K
            for orientation in mdl.O
        ) == 1

    model.service_once = pyo.Constraint(
        model.S, rule=service_once_rule
    )

    def capacity_rule(mdl, vehicle):
        return sum(
            mdl.workload[segment_index]
            * mdl.service[vehicle, segment_index, orientation]
            for segment_index in mdl.S
            for orientation in mdl.O
        ) <= mdl.capacity

    model.vehicle_capacity_constraint = pyo.Constraint(
        model.K, rule=capacity_rule
    )

    def vehicle_service_rule(mdl, vehicle):
        return sum(
            mdl.service[vehicle, segment_index, orientation]
            for segment_index in mdl.S
            for orientation in mdl.O
        ) >= 1

    model.vehicle_service_required = pyo.Constraint(
        model.K, rule=vehicle_service_rule
    )

    def service_traversal_rule(mdl, vehicle, segment_index, orientation):
        origin, destination = oriented_endpoints[
            segment_index, orientation
        ]
        return (
            mdl.travel[vehicle, origin, destination]
            >= mdl.service[vehicle, segment_index, orientation]
        )

    model.service_traversal_link = pyo.Constraint(
        model.K, model.S, model.O, rule=service_traversal_rule
    )

    def travel_balance_rule(mdl, vehicle, node):
        return sum(
            mdl.travel[vehicle, node, other]
            for other in mdl.N
            if other != node
        ) == sum(
            mdl.travel[vehicle, other, node]
            for other in mdl.N
            if other != node
        )

    model.travel_balance = pyo.Constraint(
        model.K, model.N, rule=travel_balance_rule
    )

    def depot_departure_rule(mdl, vehicle):
        return sum(
            mdl.travel[vehicle, 0, other]
            for other in mdl.N_plus
        ) >= 1

    model.depot_departure = pyo.Constraint(
        model.K, rule=depot_departure_rule
    )

    def visit_lower_rule(mdl, vehicle, node):
        return mdl.visited[vehicle, node] <= sum(
            mdl.travel[vehicle, node, other]
            for other in mdl.N
            if other != node
        )

    model.visit_lower_link = pyo.Constraint(
        model.K, model.N_plus, rule=visit_lower_rule
    )

    def visit_upper_rule(mdl, vehicle, node):
        return sum(
            mdl.travel[vehicle, node, other]
            for other in mdl.N
            if other != node
        ) <= mdl.traversal_limit * mdl.visited[vehicle, node]

    model.visit_upper_link = pyo.Constraint(
        model.K, model.N_plus, rule=visit_upper_rule
    )

    def traversal_limit_rule(mdl, vehicle):
        return sum(
            mdl.travel[vehicle, origin, destination]
            for origin, destination in mdl.A
        ) <= mdl.traversal_limit

    model.route_traversal_limit = pyo.Constraint(
        model.K, rule=traversal_limit_rule
    )

    def connectivity_capacity_rule(mdl, vehicle, origin, destination):
        return (
            mdl.connectivity[vehicle, origin, destination]
            <= mdl.connectivity_limit
            * mdl.travel[vehicle, origin, destination]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.K, model.A, rule=connectivity_capacity_rule
    )

    def connectivity_balance_rule(mdl, vehicle, node):
        return (
            sum(
                mdl.connectivity[vehicle, other, node]
                for other in mdl.N
                if other != node
            )
            - sum(
                mdl.connectivity[vehicle, node, other]
                for other in mdl.N
                if other != node
            )
            == mdl.visited[vehicle, node]
        )

    model.connectivity_balance = pyo.Constraint(
        model.K, model.N_plus, rule=connectivity_balance_rule
    )

    def depot_connectivity_rule(mdl, vehicle):
        return (
            sum(
                mdl.connectivity[vehicle, 0, other]
                for other in mdl.N_plus
            )
            - sum(
                mdl.connectivity[vehicle, other, 0]
                for other in mdl.N_plus
            )
            == sum(
                mdl.visited[vehicle, node]
                for node in mdl.N_plus
            )
        )

    model.depot_connectivity = pyo.Constraint(
        model.K, rule=depot_connectivity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[origin, destination]
            * model.travel[vehicle, origin, destination]
            for vehicle in model.K
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    # Balanced, depot-connected integer traversals form a closed route
    # for each vehicle. No termination-condition enums are inspected.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}