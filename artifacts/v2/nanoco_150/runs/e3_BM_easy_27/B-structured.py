# IR: {"sets":{"airports":[0,1,2,3,4,5,6,7,8,9],"routes":[[0,7],[0,8],[0,9],[1,5],[1,9],[2,3],[2,9],[3,4],[3,6],[3,9],[4,5],[5,6],[5,9],[6,9],[7,8],[7,9],[8,9]]},"params":{"route_revenue":"real coefficient for each route, indexed in listed order","airport_capacity":"nonnegative capacity for each airport"},"variables":{"selected[r]":"binary for each route r"},"constraints":["For each airport a: sum(selected[r] for routes r incident to a) <= airport_capacity[a]."],"objective":"maximize sum(route_revenue[r] * selected[r] for each route r)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    routes = (
        (0, 7),
        (0, 8),
        (0, 9),
        (1, 5),
        (1, 9),
        (2, 3),
        (2, 9),
        (3, 4),
        (3, 6),
        (3, 9),
        (4, 5),
        (5, 6),
        (5, 9),
        (6, 9),
        (7, 8),
        (7, 9),
        (8, 9),
    )
    airports = range(10)
    route_indices = range(len(routes))
    incident_routes = {
        airport: tuple(
            route_idx
            for route_idx, endpoints in enumerate(routes)
            if airport in endpoints
        )
        for airport in airports
    }

    model = pyo.ConcreteModel()
    model.AIRPORTS = pyo.Set(initialize=airports, ordered=True)
    model.ROUTES = pyo.Set(initialize=route_indices, ordered=True)

    model.route_revenue = pyo.Param(
        model.ROUTES,
        initialize={
            route_idx: params["route_revenue"][route_idx]
            for route_idx in route_indices
        },
        within=pyo.Reals,
    )
    model.airport_capacity = pyo.Param(
        model.AIRPORTS,
        initialize={
            airport: params["airport_capacity"][airport]
            for airport in airports
        },
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.ROUTES, domain=pyo.Binary)

    def capacity_rule(network, airport):
        return (
            sum(
                network.selected[route_idx]
                for route_idx in incident_routes[airport]
            )
            <= network.airport_capacity[airport]
        )

    model.slot_capacity = pyo.Constraint(
        model.AIRPORTS, rule=capacity_rule
    )
    model.total_revenue = pyo.Objective(
        expr=sum(
            model.route_revenue[route_idx] * model.selected[route_idx]
            for route_idx in model.ROUTES
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}