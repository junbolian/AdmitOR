# IR: {"sets":{"N":"{0,...,6}","T":"[(0,5),(2,5),(2,6),(4,6)]","R":"All nonempty ordered sequences of distinct tasks in T, with either orientation for each task"},"params":{"fleet_size":"params['fleet_size']","vehicle_capacity":"params['vehicle_capacity']","service_demands":"params['service_demands'], indexed by T in listed order","distance_matrix":"params['distance_matrix'], indexed by N x N"},"derived":{"deadhead_distance":"All-pairs shortest-path distances on the complete travel graph using distance_matrix","load[r]":"Sum of service_demands for tasks in route r","cost[r]":"Shortest deadheading from depot 0 to the first service, between successive services, and back to depot 0, plus direct distance_matrix costs for service traversals"},"variables":{"choose[r]":"Binary for every r in R"},"constraints":["For each task t: sum(choose[r] for r containing t) = 1","sum(choose[r] for r in R) = fleet_size","For each route r: load[r] * choose[r] <= vehicle_capacity"],"objective":"Minimize sum(cost[r] * choose[r] for r in R)"}

from itertools import permutations, product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fleet_size = params["fleet_size"]
    vehicle_capacity = params["vehicle_capacity"]
    service_demands = params["service_demands"]
    distance_matrix = params["distance_matrix"]

    nodes = tuple(range(7))
    required_segments = ((0, 5), (2, 5), (2, 6), (4, 6))
    task_indices = tuple(range(len(required_segments)))

    distances = {
        (origin, destination): float(distance_matrix[origin][destination])
        for origin in nodes
        for destination in nodes
    }
    demands = {
        task: float(service_demands[task])
        for task in task_indices
    }

    # Deadheading can pass through intermediate nodes. Servicing a required
    # segment always incurs that segment's direct distance.
    deadhead_distance = dict(distances)
    for intermediate in nodes:
        for origin in nodes:
            for destination in nodes:
                candidate = (
                    deadhead_distance[origin, intermediate]
                    + deadhead_distance[intermediate, destination]
                )
                if candidate < deadhead_distance[origin, destination]:
                    deadhead_distance[origin, destination] = candidate

    route_costs = {}
    route_loads = {}
    task_routes = {task: [] for task in task_indices}

    # Enumerating service orders and orientations is exact: between successive
    # services, any deadheading walk can be replaced by a shortest path.
    for route_length in range(1, len(task_indices) + 1):
        for task_order in permutations(task_indices, route_length):
            route_load = sum(demands[task] for task in task_order)

            for orientations in product((0, 1), repeat=route_length):
                current_node = 0
                route_cost = 0.0

                for task, orientation in zip(task_order, orientations):
                    endpoint_a, endpoint_b = required_segments[task]
                    if orientation == 0:
                        service_start, service_end = endpoint_a, endpoint_b
                    else:
                        service_start, service_end = endpoint_b, endpoint_a

                    route_cost += deadhead_distance[
                        current_node, service_start
                    ]
                    route_cost += distances[service_start, service_end]
                    current_node = service_end

                route_cost += deadhead_distance[current_node, 0]

                route_id = len(route_costs)
                route_costs[route_id] = route_cost
                route_loads[route_id] = route_load
                for task in task_order:
                    task_routes[task].append(route_id)

    model = pyo.ConcreteModel()

    model.tasks = pyo.Set(initialize=task_indices, ordered=True)
    model.routes = pyo.Set(initialize=tuple(route_costs), ordered=True)

    model.fleet_count = pyo.Param(
        initialize=fleet_size,
        within=pyo.NonNegativeIntegers,
    )
    model.capacity_limit = pyo.Param(
        initialize=vehicle_capacity,
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize=route_costs,
        within=pyo.NonNegativeReals,
    )
    model.route_load = pyo.Param(
        model.routes,
        initialize=route_loads,
        within=pyo.NonNegativeReals,
    )

    model.choose = pyo.Var(model.routes, domain=pyo.Binary)

    def service_once_rule(instance, task):
        return pyo.quicksum(
            instance.choose[route_id]
            for route_id in task_routes[task]
        ) == 1

    model.service_once = pyo.Constraint(
        model.tasks,
        rule=service_once_rule,
    )

    model.fleet_requirement = pyo.Constraint(
        expr=pyo.quicksum(
            model.choose[route_id] for route_id in model.routes
        ) == model.fleet_count
    )

    def route_capacity_rule(instance, route_id):
        return (
            instance.route_load[route_id] * instance.choose[route_id]
            <= instance.capacity_limit
        )

    model.route_capacity = pyo.Constraint(
        model.routes,
        rule=route_capacity_rule,
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[route_id] * model.choose[route_id]
            for route_id in model.routes
        ),
        sense=pyo.minimize,
    )

    # Catch only failures from solving or retrieving the objective.
    # Do not inspect termination-condition enums.
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_distance))
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}