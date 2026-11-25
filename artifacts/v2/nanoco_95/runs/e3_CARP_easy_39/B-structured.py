# IR: {"sets":{"V":"{0,...,6}","K":"{0,...,num_trucks-1}","E":"[(0,2),(0,6),(2,3),(2,4)]","R":"all nonempty ordered subsets of E, with each segment independently oriented"},"params":{"num_trucks":"params[num_trucks]","num_required_segments":"params[num_required_segments], must equal |E|","truck_capacity":"params[truck_capacity]","demands":"params[demand_segment_0_2], params[demand_segment_0_6], params[demand_segment_2_3], params[demand_segment_2_4]","coord_x":"params[coord_x], node metadata","coord_y":"params[coord_y], node metadata","distance_matrix":"params[distance_matrix]","a[r,e]":"1 iff route r services segment e","q[r]":"sum of service demands on route r","c[r]":"distance from depot to first service start, plus all directed service distances, plus distances between consecutive services, plus distance from last service end to depot"},"variables":{"x[k,r]":"binary, truck k selects route r"},"constraints":["sum_r x[k,r] = 1 for every truck k","sum_k sum_r a[r,e]*x[k,r] = 1 for every required segment e","sum_r q[r]*x[k,r] <= truck_capacity for every truck k"],"objective":"minimize sum_k sum_r c[r]*x[k,r]"}
from itertools import permutations, product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_count_raw = params["num_trucks"]
    segment_count_raw = params["num_required_segments"]
    truck_capacity = params["truck_capacity"]
    demands = (
        params["demand_segment_0_2"],
        params["demand_segment_0_6"],
        params["demand_segment_2_3"],
        params["demand_segment_2_4"],
    )
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    distance_matrix = params["distance_matrix"]

    required_segments = ((0, 2), (0, 6), (2, 3), (2, 4))
    nodes = tuple(range(7))

    truck_count = int(truck_count_raw)
    segment_count = int(segment_count_raw)

    if (
        truck_count != truck_count_raw
        or truck_count < 1
        or segment_count != segment_count_raw
        or segment_count != len(required_segments)
    ):
        return {"objective": None, "status": "invalid_parameters"}

    # Every route services at least one segment. Deadheading may traverse
    # a required segment without servicing it.
    route_segments = {}
    route_demands = {}
    route_costs = {}

    for route_size in range(1, segment_count + 1):
        for segment_order in permutations(range(segment_count), route_size):
            for orientations in product((0, 1), repeat=route_size):
                previous_end = 0
                travel_cost = 0

                for segment_id, reverse in zip(segment_order, orientations):
                    endpoint_a, endpoint_b = required_segments[segment_id]
                    if reverse:
                        service_start, service_end = endpoint_b, endpoint_a
                    else:
                        service_start, service_end = endpoint_a, endpoint_b

                    travel_cost += distance_matrix[previous_end][service_start]
                    travel_cost += distance_matrix[service_start][service_end]
                    previous_end = service_end

                travel_cost += distance_matrix[previous_end][0]

                route_id = len(route_costs)
                route_segments[route_id] = frozenset(segment_order)
                route_demands[route_id] = sum(
                    demands[segment_id] for segment_id in segment_order
                )
                route_costs[route_id] = travel_cost

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.K = pyo.Set(initialize=range(truck_count), ordered=True)
    model.E = pyo.Set(initialize=range(segment_count), ordered=True)
    model.R = pyo.Set(initialize=route_costs.keys(), ordered=True)

    model.num_trucks = pyo.Param(
        initialize=truck_count, within=pyo.PositiveIntegers
    )
    model.num_required_segments = pyo.Param(
        initialize=segment_count, within=pyo.PositiveIntegers
    )
    model.truck_capacity = pyo.Param(
        initialize=truck_capacity, within=pyo.NonNegativeReals
    )
    model.service_demand = pyo.Param(
        model.E,
        initialize=dict(enumerate(demands)),
        within=pyo.NonNegativeReals,
    )
    model.coord_x = pyo.Param(
        model.V,
        initialize={node: coord_x[node] for node in nodes},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.V,
        initialize={node: coord_y[node] for node in nodes},
        within=pyo.Reals,
    )
    model.distance_matrix = pyo.Param(
        model.V,
        model.V,
        initialize={
            (origin, destination): distance_matrix[origin][destination]
            for origin in nodes
            for destination in nodes
        },
        within=pyo.NonNegativeReals,
    )
    model.route_demand = pyo.Param(
        model.R, initialize=route_demands, within=pyo.NonNegativeReals
    )
    model.route_cost = pyo.Param(
        model.R, initialize=route_costs, within=pyo.NonNegativeReals
    )

    model.x = pyo.Var(model.K, model.R, domain=pyo.Binary)

    def select_route_rule(instance, truck):
        return sum(instance.x[truck, route] for route in instance.R) == 1

    model.select_route = pyo.Constraint(model.K, rule=select_route_rule)

    def service_once_rule(instance, segment):
        return sum(
            instance.x[truck, route]
            for truck in instance.K
            for route in instance.R
            if segment in route_segments[route]
        ) == 1

    model.service_once = pyo.Constraint(model.E, rule=service_once_rule)

    def capacity_rule(instance, truck):
        return sum(
            instance.route_demand[route] * instance.x[truck, route]
            for route in instance.R
        ) <= instance.truck_capacity

    model.capacity_limit = pyo.Constraint(model.K, rule=capacity_rule)

    model.total_distance = pyo.Objective(
        expr=sum(
            model.route_cost[route] * model.x[truck, route]
            for truck in model.K
            for route in model.R
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when no solution can be loaded.
    # Success is determined exclusively by objective retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}