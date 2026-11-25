# IR: {"sets":{"nodes":"0..9","intermediate_nodes":"1..8","routes":[[0,1],[1,2],[1,7],[2,3],[2,6],[3,4],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},"params":{"capacities":"params['capacities'], indexed in route order","costs":"params['costs'], indexed in route order"},"variables":{"flow[route]":"continuous, nonnegative"},"constraints":["flow[route] <= capacities[route] for every route","sum(incoming flow) = sum(outgoing flow) at nodes 1..8","stage 2: total source outflow = stage 1 optimal source outflow"],"objective":"Lexicographically maximize total source outflow, then minimize sum(costs[route]*flow[route]); return the maximum flow as objective."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]

    routes = (
        (0, 1),
        (1, 2),
        (1, 7),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 8),
        (5, 6),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    )

    if len(capacities) != len(routes) or len(costs) != len(routes):
        return {"objective": None, "status": "invalid_parameter_lengths"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.intermediate_nodes = pyo.RangeSet(1, 8)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.route_capacity = pyo.Param(
        model.routes,
        initialize={
            route: capacities[position]
            for position, route in enumerate(routes)
        },
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={
            route: costs[position]
            for position, route in enumerate(routes)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.route_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.routes, rule=capacity_rule
    )

    def conservation_rule(instance, node):
        inflow = sum(
            instance.flow[origin, destination]
            for origin, destination in routes
            if destination == node
        )
        outflow = sum(
            instance.flow[origin, destination]
            for origin, destination in routes
            if origin == node
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.delivered_volume = pyo.Expression(
        expr=sum(
            model.flow[origin, destination]
            for origin, destination in routes
            if origin == 0
        )
    )

    model.maximum_delivery = pyo.Objective(
        expr=model.delivered_volume,
        sense=pyo.maximize,
    )

    # Stage 1: determine the maximum feasible delivered volume.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.maximum_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    maximum_flow = obj_val

    # Stage 2: find the least-cost flow distribution at that volume.
    model.required_delivery = pyo.Constraint(
        expr=model.delivered_volume == maximum_flow
    )
    model.maximum_delivery.deactivate()
    model.minimum_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.minimum_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # Report the primary objective after optimizing the secondary objective.
    try:
        obj_val = float(pyo.value(model.maximum_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}