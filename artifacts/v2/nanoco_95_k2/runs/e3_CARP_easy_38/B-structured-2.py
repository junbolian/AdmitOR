# IR: {"sets":{"V":"range(params['num_nodes'])","K":"range(params['num_vehicles'])","R":"[(0,3),(0,4),(2,3),(3,4)] in demand order","O":"[0,1], forward/reverse","A":"all ordered pairs of distinct nodes"},"params":{"vehicle_capacity":"nonnegative real","demands":"nonnegative real per required segment","num_vehicles":"positive integer","num_service_segments":"must equal len(R)","num_nodes":"positive integer","distance_matrix":"nonnegative direct travel costs on V x V","node_coordinates":"coordinates on V, retained as data; distances come only from distance_matrix"},"variables":{"traversals[k,i,j]":"nonnegative integer","service[k,r,o]":"binary","flow[k,i,j]":"nonnegative real"},"constraints":["Each required segment has exactly one service assignment across vehicles and orientations.","Each vehicle services at least one required segment.","Each vehicle's assigned workload is at most vehicle_capacity.","Traversals on each oriented required segment cover its service assignment.","Each vehicle has equal incoming and outgoing traversal counts at every node.","Connectivity flow on an arc is at most 2*len(R) times its traversal count.","Each nondepot node consumes one flow unit per incident assigned service endpoint; the depot supplies the total consumption."],"objective":"Minimize sum(distance_matrix[i][j]*traversals[k,i,j]) over vehicles and directed arcs."}

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
    depot = 0

    if num_service_segments != len(required_segments):
        raise ValueError(
            "num_service_segments must match the four specified service segments."
        )
    if len(demands) != num_service_segments:
        raise ValueError("demands must contain one value per service segment.")
    if num_nodes <= max(
        endpoint for segment in required_segments for endpoint in segment
    ):
        raise ValueError("num_nodes does not include all required endpoints.")
    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix must have num_nodes rows and columns.")
    if len(node_coordinates) != num_nodes or any(
        len(coordinate) != 2 for coordinate in node_coordinates
    ):
        raise ValueError("node_coordinates must contain one coordinate pair per node.")

    model = pyo.ConcreteModel()

    model.fleet_size = pyo.Param(
        initialize=num_vehicles, within=pyo.PositiveIntegers
    )
    model.network_size = pyo.Param(
        initialize=num_nodes, within=pyo.PositiveIntegers
    )
    model.service_count = pyo.Param(
        initialize=num_service_segments, within=pyo.PositiveIntegers
    )

    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.vehicles = pyo.Set(initialize=range(num_vehicles), ordered=True)
    model.services = pyo.Set(
        initialize=range(num_service_segments), ordered=True
    )
    model.orientations = pyo.Set(initialize=(0, 1), ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (source, target)
            for source in range(num_nodes)
            for target in range(num_nodes)
            if source != target
        ),
    )

    model.capacity_limit = pyo.Param(
        initialize=vehicle_capacity, within=pyo.NonNegativeReals
    )
    model.workload = pyo.Param(
        model.services,
        initialize=lambda instance, task: demands[task],
        within=pyo.NonNegativeReals,
    )
    model.travel_cost = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda instance, source, target: distance_matrix[source][target],
        within=pyo.NonNegativeReals,
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize=lambda instance, node, axis: node_coordinates[node][axis],
        within=pyo.Reals,
    )

    oriented_endpoints = {
        (task, orientation): (
            required_segments[task]
            if orientation == 0
            else required_segments[task][::-1]
        )
        for task in range(num_service_segments)
        for orientation in (0, 1)
    }

    model.traversals = pyo.Var(
        model.vehicles, model.arcs, domain=pyo.NonNegativeIntegers
    )
    model.service = pyo.Var(
        model.vehicles,
        model.services,
        model.orientations,
        domain=pyo.Binary,
    )
    model.flow = pyo.Var(
        model.vehicles, model.arcs, domain=pyo.NonNegativeReals
    )

    def exact_service_rule(instance, task):
        return sum(
            instance.service[vehicle, task, orientation]
            for vehicle in instance.vehicles
            for orientation in instance.orientations
        ) == 1

    model.exact_service = pyo.Constraint(
        model.services, rule=exact_service_rule
    )

    def vehicle_service_rule(instance, vehicle):
        return sum(
            instance.service[vehicle, task, orientation]
            for task in instance.services
            for orientation in instance.orientations
        ) >= 1

    model.vehicle_service = pyo.Constraint(
        model.vehicles, rule=vehicle_service_rule
    )

    def capacity_rule(instance, vehicle):
        return sum(
            instance.workload[task]
            * instance.service[vehicle, task, orientation]
            for task in instance.services
            for orientation in instance.orientations
        ) <= instance.capacity_limit

    model.vehicle_capacity_constraints = pyo.Constraint(
        model.vehicles, rule=capacity_rule
    )

    def service_traversal_rule(instance, vehicle, task, orientation):
        source, target = oriented_endpoints[task, orientation]
        return (
            instance.traversals[vehicle, source, target]
            >= instance.service[vehicle, task, orientation]
        )

    model.service_traversal = pyo.Constraint(
        model.vehicles,
        model.services,
        model.orientations,
        rule=service_traversal_rule,
    )

    def traversal_balance_rule(instance, vehicle, node):
        return sum(
            instance.traversals[vehicle, node, other]
            for other in instance.nodes
            if other != node
        ) == sum(
            instance.traversals[vehicle, other, node]
            for other in instance.nodes
            if other != node
        )

    model.traversal_balance = pyo.Constraint(
        model.vehicles, model.nodes, rule=traversal_balance_rule
    )

    def endpoint_consumption_rule(instance, vehicle, node):
        return sum(
            instance.service[vehicle, task, orientation]
            for task in instance.services
            for orientation in instance.orientations
            for endpoint in oriented_endpoints[task, orientation]
            if endpoint == node
        )

    model.endpoint_consumption = pyo.Expression(
        model.vehicles, model.nodes, rule=endpoint_consumption_rule
    )

    def flow_link_rule(instance, vehicle, source, target):
        return (
            instance.flow[vehicle, source, target]
            <= 2
            * instance.service_count
            * instance.traversals[vehicle, source, target]
        )

    model.flow_link = pyo.Constraint(
        model.vehicles, model.arcs, rule=flow_link_rule
    )

    def connectivity_balance_rule(instance, vehicle, node):
        outgoing = sum(
            instance.flow[vehicle, node, other]
            for other in instance.nodes
            if other != node
        )
        incoming = sum(
            instance.flow[vehicle, other, node]
            for other in instance.nodes
            if other != node
        )
        if node == depot:
            return outgoing - incoming == sum(
                instance.endpoint_consumption[vehicle, other]
                for other in instance.nodes
                if other != depot
            )
        return (
            incoming - outgoing
            == instance.endpoint_consumption[vehicle, node]
        )

    model.connectivity_balance = pyo.Constraint(
        model.vehicles, model.nodes, rule=connectivity_balance_rule
    )

    # Balanced integer traversals and depot connectivity admit a closed
    # vehicle walk containing every assigned service traversal. Repeated
    # deadheading and intermediate nodes are allowed and charged explicitly.
    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[source, target]
            * model.traversals[vehicle, source, target]
            for vehicle in model.vehicles
            for source, target in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Other runtime errors remain visible to the calling harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}