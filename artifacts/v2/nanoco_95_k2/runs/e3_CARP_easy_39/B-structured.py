# IR: {"sets":{"N":"range(num_nodes)","K":"range(num_trucks)","E":"[(0,2),(0,6),(2,3),(2,4)]","R":"nonempty subsets of E with total demand <= truck_capacity"},"params":{"demand_0_2":"service demand","demand_0_6":"service demand","demand_2_3":"service demand","demand_2_4":"service demand","truck_capacity":"vehicle capacity","num_trucks":"fleet cardinality","num_service_segments":"fixed service cardinality","num_nodes":"fixed node cardinality","distance_matrix":"travel and service distances, nested or flat row-major","depot_coord_x":"depot x metadata","depot_coord_y":"depot y metadata","node_coords_x":"nondepot x metadata","node_coords_y":"nondepot y metadata","route_cost[r]":"minimum depot-return distance over every ordering and orientation of subset r"},"variables":{"choose[k,r]":"Binary"},"constraints":["For each truck k: sum_r choose[k,r] = 1.","For each service segment e: sum_{k,r:e in r} choose[k,r] = 1.","Capacity is enforced by membership in R."],"objective":"Minimize sum_{k,r} route_cost[r] * choose[k,r]."}
from itertools import combinations, permutations, product
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    def read_count(key):
        raw = params[key]
        count = int(raw)
        if count != raw or count < 1:
            raise ValueError(f"{key} must be a positive integer.")
        return count

    num_trucks = read_count("num_trucks")
    num_service_segments = read_count("num_service_segments")
    num_nodes = read_count("num_nodes")

    segments = ((0, 2), (0, 6), (2, 3), (2, 4))
    if num_service_segments != len(segments):
        raise ValueError("num_service_segments must match the four specified segments.")
    if num_nodes != 7:
        raise ValueError("num_nodes must match the specified seven-node network.")

    demands = (
        float(params["demand_0_2"]),
        float(params["demand_0_6"]),
        float(params["demand_2_3"]),
        float(params["demand_2_4"]),
    )
    capacity = float(params["truck_capacity"])
    raw_distances = params["distance_matrix"]
    depot_x = float(params["depot_coord_x"])
    depot_y = float(params["depot_coord_y"])
    other_x = tuple(float(value) for value in params["node_coords_x"])
    other_y = tuple(float(value) for value in params["node_coords_y"])

    if len(other_x) != num_nodes - 1 or len(other_y) != num_nodes - 1:
        raise ValueError("Node coordinate arrays must contain num_nodes - 1 values.")

    coordinates_x = (depot_x,) + other_x
    coordinates_y = (depot_y,) + other_y
    if not all(math.isfinite(value) for value in coordinates_x + coordinates_y):
        raise ValueError("Coordinates must be finite.")
    if not math.isfinite(capacity) or capacity < 0:
        raise ValueError("truck_capacity must be finite and nonnegative.")
    if not all(math.isfinite(value) and value >= 0 for value in demands):
        raise ValueError("Service demands must be finite and nonnegative.")

    if len(raw_distances) == num_nodes * num_nodes:
        distances = tuple(
            tuple(
                float(raw_distances[row_id * num_nodes + column_id])
                for column_id in range(num_nodes)
            )
            for row_id in range(num_nodes)
        )
    elif len(raw_distances) == num_nodes:
        if any(len(row) != num_nodes for row in raw_distances):
            raise ValueError("Each distance-matrix row must contain num_nodes values.")
        distances = tuple(
            tuple(float(value) for value in row)
            for row in raw_distances
        )
    else:
        raise ValueError("distance_matrix must be square or flat row-major.")

    if not all(
        math.isfinite(value) and value >= 0
        for row in distances
        for value in row
    ):
        raise ValueError("Travel distances must be finite and nonnegative.")

    # Each subset represents one nonempty truck route. For a fixed subset,
    # exhaustive ordering and orientation enumeration gives its exact best cost.
    route_segments = {}
    route_costs = {}
    service_ids = tuple(range(num_service_segments))

    for subset_size in range(1, num_service_segments + 1):
        for subset in combinations(service_ids, subset_size):
            if sum(demands[service_id] for service_id in subset) > capacity:
                continue

            best_cost = math.inf
            for ordering in permutations(subset):
                for orientations in product((0, 1), repeat=subset_size):
                    current_node = 0
                    travel_cost = 0.0

                    for service_id, reverse in zip(ordering, orientations):
                        endpoint_a, endpoint_b = segments[service_id]
                        if reverse:
                            start_node, end_node = endpoint_b, endpoint_a
                        else:
                            start_node, end_node = endpoint_a, endpoint_b

                        travel_cost += distances[current_node][start_node]
                        travel_cost += distances[start_node][end_node]
                        current_node = end_node

                    travel_cost += distances[current_node][0]
                    best_cost = min(best_cost, travel_cost)

            route_id = len(route_costs)
            route_segments[route_id] = subset
            route_costs[route_id] = best_cost

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, num_nodes - 1)
    model.K = pyo.RangeSet(0, num_trucks - 1)
    model.E = pyo.RangeSet(0, num_service_segments - 1)
    model.R = pyo.Set(initialize=tuple(route_costs), ordered=True)

    model.service_demand = pyo.Param(
        model.E,
        initialize={service_id: demands[service_id] for service_id in service_ids},
    )
    model.vehicle_capacity = pyo.Param(initialize=capacity)
    model.travel_distance = pyo.Param(
        model.N,
        model.N,
        initialize={
            (row_id, column_id): distances[row_id][column_id]
            for row_id in range(num_nodes)
            for column_id in range(num_nodes)
        },
    )
    model.coordinate_x = pyo.Param(
        model.N,
        initialize=dict(enumerate(coordinates_x)),
    )
    model.coordinate_y = pyo.Param(
        model.N,
        initialize=dict(enumerate(coordinates_y)),
    )
    model.route_cost = pyo.Param(model.R, initialize=route_costs)
    model.choose = pyo.Var(model.K, model.R, domain=pyo.Binary)

    def one_route_rule(block, truck_id):
        if not route_costs:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            block.choose[truck_id, route_id]
            for route_id in block.R
        ) == 1

    model.one_route_per_truck = pyo.Constraint(
        model.K,
        rule=one_route_rule,
    )

    eligible_routes = {
        service_id: tuple(
            route_id
            for route_id, subset in route_segments.items()
            if service_id in subset
        )
        for service_id in service_ids
    }

    def service_once_rule(block, service_id):
        if not eligible_routes[service_id]:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            block.choose[truck_id, route_id]
            for truck_id in block.K
            for route_id in eligible_routes[service_id]
        ) == 1

    model.service_exactly_once = pyo.Constraint(
        model.E,
        rule=service_once_rule,
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[route_id] * model.choose[truck_id, route_id]
            for truck_id in model.K
            for route_id in model.R
        ),
        sense=pyo.minimize,
    )

    # Appsi HiGHS raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}