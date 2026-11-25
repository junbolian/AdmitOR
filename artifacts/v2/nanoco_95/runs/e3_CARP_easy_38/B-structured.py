# IR: {"sets":{"V":[0,1,2,3,4,5,6],"K":[0,1],"E_required":[[0,3],[0,4],[2,3],[3,4]],"S":"all nonempty subsets of E_required"},"params":{"distance_matrix":"params['distance_matrix']","segment_demands":"params['segment_demands']","vehicle_capacity":"params['vehicle_capacity']"},"derived":{"deadhead_distance":"all-pairs shortest-path distances using distance_matrix on the complete directed graph","route_cost[S]":"minimum depot-to-depot cost over all orders and orientations of the segments in S; service uses direct segment distances and connections use deadhead_distance","route_demand[S]":"sum of segment_demands for segments in S"},"variables":{"route_selected[k,S]":"binary"},"constraints":{"one_route_per_vehicle":"sum_S route_selected[k,S] = 1 for each k","exact_service":"sum_{k,S containing e} route_selected[k,S] = 1 for each required segment e","capacity":"sum_S route_demand[S]*route_selected[k,S] <= vehicle_capacity for each k"},"objective":"minimize sum_{k,S} route_cost[S]*route_selected[k,S]"}

from itertools import permutations, product

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = [
        [float(value) for value in row]
        for row in params["distance_matrix"]
    ]
    segment_demands = [
        float(value) for value in params["segment_demands"]
    ]
    vehicle_capacity = float(params["vehicle_capacity"])

    nodes = tuple(range(7))
    vehicles = tuple(range(2))
    required_segments = ((0, 3), (0, 4), (2, 3), (3, 4))
    segment_ids = tuple(range(len(required_segments)))

    if (
        len(distance_matrix) != len(nodes)
        or any(len(row) != len(nodes) for row in distance_matrix)
    ):
        raise ValueError("distance_matrix must be a 7x7 matrix.")
    if len(segment_demands) != len(required_segments):
        raise ValueError("segment_demands must contain four entries.")

    # Deadheading may pass through intermediate nodes. Service traversal
    # itself always incurs the supplied direct distance of its segment.
    deadhead_distance = [row[:] for row in distance_matrix]
    for intermediate in nodes:
        for origin in nodes:
            for destination in nodes:
                candidate = (
                    deadhead_distance[origin][intermediate]
                    + deadhead_distance[intermediate][destination]
                )
                if candidate < deadhead_distance[origin][destination]:
                    deadhead_distance[origin][destination] = candidate

    subset_ids = tuple(range(1, 1 << len(required_segments)))
    subset_members = {
        subset_id: tuple(
            segment_id
            for segment_id in segment_ids
            if subset_id & (1 << segment_id)
        )
        for subset_id in subset_ids
    }

    route_demand = {}
    route_cost = {}

    # Enumerating orders and directions gives an exact minimum route cost
    # for each subset. Both vehicles select a nonempty service route.
    for subset_id in subset_ids:
        members = subset_members[subset_id]
        route_demand[subset_id] = sum(
            segment_demands[segment_id] for segment_id in members
        )
        best_cost = float("inf")

        for ordering in permutations(members):
            for directions in product((0, 1), repeat=len(ordering)):
                current_node = 0
                total_cost = 0.0

                for segment_id, direction in zip(ordering, directions):
                    endpoint_a, endpoint_b = required_segments[segment_id]
                    if direction == 0:
                        service_start, service_end = endpoint_a, endpoint_b
                    else:
                        service_start, service_end = endpoint_b, endpoint_a

                    total_cost += deadhead_distance[current_node][service_start]
                    total_cost += distance_matrix[service_start][service_end]
                    current_node = service_end

                total_cost += deadhead_distance[current_node][0]
                best_cost = min(best_cost, total_cost)

        route_cost[subset_id] = best_cost

    model = pyo.ConcreteModel()
    model.vehicle_ids = pyo.Set(initialize=vehicles, ordered=True)
    model.route_ids = pyo.Set(initialize=subset_ids, ordered=True)
    model.service_ids = pyo.Set(initialize=segment_ids, ordered=True)

    model.route_selected = pyo.Var(
        model.vehicle_ids,
        model.route_ids,
        domain=pyo.Binary,
    )

    def one_route_rule(instance, vehicle_id):
        return sum(
            instance.route_selected[vehicle_id, subset_id]
            for subset_id in instance.route_ids
        ) == 1

    model.one_route_per_vehicle = pyo.Constraint(
        model.vehicle_ids, rule=one_route_rule
    )

    def exact_service_rule(instance, segment_id):
        return sum(
            instance.route_selected[vehicle_id, subset_id]
            for vehicle_id in instance.vehicle_ids
            for subset_id in instance.route_ids
            if segment_id in subset_members[subset_id]
        ) == 1

    model.exact_service = pyo.Constraint(
        model.service_ids, rule=exact_service_rule
    )

    def capacity_rule(instance, vehicle_id):
        return sum(
            route_demand[subset_id]
            * instance.route_selected[vehicle_id, subset_id]
            for subset_id in instance.route_ids
        ) <= vehicle_capacity

    model.vehicle_capacity_limit = pyo.Constraint(
        model.vehicle_ids, rule=capacity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            route_cost[subset_id]
            * model.route_selected[vehicle_id, subset_id]
            for vehicle_id in model.vehicle_ids
            for subset_id in model.route_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}