# IR: {"sets":{"nodes":[0,1,2,3,4,5],"dimensions":[0,1],"routes":[[0,1],[0,2],[0,5],[1,0],[1,2],[2,1],[2,3],[3,1],[3,2],[3,4],[4,2],[4,3],[4,5],[5,0],[5,2],[5,3],[5,4]]},"params":{"coordinates":"real[nodes,dimensions]; layout metadata only","route_cost":"real[routes], supplied in route order","route_min_flow":"nonnegative real[routes], supplied in route order","route_max_capacity":"nonnegative real[routes], supplied in route order"},"variables":{"flow":"nonnegative integer[routes]"},"constraints":["For each node: sum(flow on incoming routes) = sum(flow on outgoing routes).","For each route: flow >= route_min_flow.","For each route: flow <= route_max_capacity."],"objective":"Minimize sum(route_cost[route] * flow[route] for route in routes)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coordinates = params["coordinates"]
    route_cost = params["route_cost"]
    route_min_flow = params["route_min_flow"]
    route_max_capacity = params["route_max_capacity"]

    nodes = tuple(range(6))
    dimensions = (0, 1)
    routes = (
        (0, 1),
        (0, 2),
        (0, 5),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, 4),
        (4, 2),
        (4, 3),
        (4, 5),
        (5, 0),
        (5, 2),
        (5, 3),
        (5, 4),
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.dimensions = pyo.Set(initialize=dimensions, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize={
            (node, dimension): coordinates[node][dimension]
            for node in nodes
            for dimension in dimensions
        },
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={
            route: route_cost[position]
            for position, route in enumerate(routes)
        },
        within=pyo.Reals,
    )
    model.route_min_flow = pyo.Param(
        model.routes,
        initialize={
            route: route_min_flow[position]
            for position, route in enumerate(routes)
        },
        within=pyo.NonNegativeReals,
    )
    model.route_max_capacity = pyo.Param(
        model.routes,
        initialize={
            route: route_max_capacity[position]
            for position, route in enumerate(routes)
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeIntegers)

    def circulation_rule(instance, node):
        incoming = sum(
            instance.flow[source, destination]
            for source, destination in routes
            if destination == node
        )
        outgoing = sum(
            instance.flow[source, destination]
            for source, destination in routes
            if source == node
        )
        return incoming == outgoing

    model.circulation = pyo.Constraint(
        model.nodes, rule=circulation_rule
    )
    model.minimum_flow = pyo.Constraint(
        model.routes,
        rule=lambda instance, source, destination:
        instance.flow[source, destination]
        >= instance.route_min_flow[source, destination],
    )
    model.maximum_flow = pyo.Constraint(
        model.routes,
        rule=lambda instance, source, destination:
        instance.flow[source, destination]
        <= instance.route_max_capacity[source, destination],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}