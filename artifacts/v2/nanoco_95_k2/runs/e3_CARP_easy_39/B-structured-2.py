# IR: {"sets":{"N":"range(num_nodes), frozen at 7","K":"range(num_trucks)","E":"[(0,2),(0,6),(2,3),(2,4)], frozen at 4","R":"all nonempty ordered subsets of E, with every service-direction combination"},"params":{"input":["demand_0_2","demand_0_6","demand_2_3","demand_2_4","truck_capacity","num_trucks","num_service_segments","num_nodes","distance_matrix","depot_coord_x","depot_coord_y","node_coords_x","node_coords_y"],"derived":{"demand[e]":"corresponding input demand","distance[i,j]":"input matrix entry","coord_x[i],coord_y[i]":"input coordinates, retained as metadata","covers[r,e]":"1 iff route r services segment e","route_load[r]":"sum of demands serviced by r","route_cost[r]":"depot-to-first-service travel + all service travel + inter-service travel + last-service-to-depot travel"}},"variables":{"route_used[k,r]":"binary"},"constraints":["For each truck k: sum_r route_used[k,r] = 1.","For each segment e: sum_k,r covers[r,e]*route_used[k,r] = 1.","For each truck k: sum_r route_load[r]*route_used[k,r] <= truck_capacity."],"objective":"minimize sum_k,r route_cost[r]*route_used[k,r]"}
from itertools import permutations, product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_trucks = int(params["num_trucks"])
    num_service_segments = int(params["num_service_segments"])

    if num_nodes != 7 or num_service_segments != 4 or num_trucks < 1:
        return {"objective": None, "status": "invalid_cardinality"}

    service_segments = ((0, 2), (0, 6), (2, 3), (2, 4))
    demand_values = (
        float(params["demand_0_2"]),
        float(params["demand_0_6"]),
        float(params["demand_2_3"]),
        float(params["demand_2_4"]),
    )
    capacity_value = float(params["truck_capacity"])

    raw_distances = params["distance_matrix"]
    if len(raw_distances) == num_nodes * num_nodes:
        distances = {
            (origin, destination): float(
                raw_distances[origin * num_nodes + destination]
            )
            for origin in range(num_nodes)
            for destination in range(num_nodes)
        }
    else:
        if (
            len(raw_distances) != num_nodes
            or any(len(row) != num_nodes for row in raw_distances)
        ):
            return {"objective": None, "status": "invalid_distance_matrix"}
        distances = {
            (origin, destination): float(raw_distances[origin][destination])
            for origin in range(num_nodes)
            for destination in range(num_nodes)
        }

    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]
    if (
        len(node_coords_x) != num_nodes - 1
        or len(node_coords_y) != num_nodes - 1
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    coord_x = {0: float(params["depot_coord_x"])}
    coord_y = {0: float(params["depot_coord_y"])}
    coord_x.update(
        {
            node: float(node_coords_x[node - 1])
            for node in range(1, num_nodes)
        }
    )
    coord_y.update(
        {
            node: float(node_coords_y[node - 1])
            for node in range(1, num_nodes)
        }
    )

    # Enumerate every possible nonempty service sequence and orientation.
    # Travel uses the supplied matrix directly, including service travel.
    route_cost = {}
    route_load = {}
    covers = {}

    for route_length in range(1, num_service_segments + 1):
        for sequence in permutations(range(num_service_segments), route_length):
            load = sum(demand_values[segment] for segment in sequence)
            for directions in product((0, 1), repeat=route_length):
                route_id = len(route_cost)
                current_node = 0
                cost = 0.0

                for segment, direction in zip(sequence, directions):
                    endpoint_a, endpoint_b = service_segments[segment]
                    if direction == 0:
                        start_node, end_node = endpoint_a, endpoint_b
                    else:
                        start_node, end_node = endpoint_b, endpoint_a

                    cost += distances[current_node, start_node]
                    cost += distances[start_node, end_node]
                    current_node = end_node

                cost += distances[current_node, 0]
                route_cost[route_id] = cost
                route_load[route_id] = load
                for segment in sequence:
                    covers[route_id, segment] = 1

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.K = pyo.Set(initialize=range(num_trucks), ordered=True)
    model.E = pyo.Set(initialize=range(num_service_segments), ordered=True)
    model.R = pyo.Set(initialize=range(len(route_cost)), ordered=True)

    model.truck_capacity = pyo.Param(initialize=capacity_value)
    model.demand = pyo.Param(
        model.E,
        initialize=dict(enumerate(demand_values)),
    )
    model.distance = pyo.Param(model.N, model.N, initialize=distances)
    model.coord_x = pyo.Param(model.N, initialize=coord_x)
    model.coord_y = pyo.Param(model.N, initialize=coord_y)
    model.covers = pyo.Param(
        model.R, model.E, initialize=covers, default=0
    )
    model.route_load = pyo.Param(model.R, initialize=route_load)
    model.route_cost = pyo.Param(model.R, initialize=route_cost)

    model.route_used = pyo.Var(model.K, model.R, domain=pyo.Binary)

    def one_route_rule(instance, truck):
        return sum(
            instance.route_used[truck, route] for route in instance.R
        ) == 1

    model.one_route = pyo.Constraint(model.K, rule=one_route_rule)

    def service_once_rule(instance, segment):
        return sum(
            instance.covers[route, segment]
            * instance.route_used[truck, route]
            for truck in instance.K
            for route in instance.R
        ) == 1

    model.service_once = pyo.Constraint(model.E, rule=service_once_rule)

    def capacity_rule(instance, truck):
        return sum(
            instance.route_load[route] * instance.route_used[truck, route]
            for route in instance.R
        ) <= instance.truck_capacity

    model.capacity_limit = pyo.Constraint(model.K, rule=capacity_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.route_cost[route] * model.route_used[truck, route]
            for truck in model.K
            for route in model.R
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}