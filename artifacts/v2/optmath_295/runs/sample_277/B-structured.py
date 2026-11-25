# IR: {"sets":{"cities":"range(n_cities)","arcs":"[(i,j) for i in cities for j in cities if i != j]"},"params":{"n_cities":"params['n_cities']","distance[i,j]":"params[f'dist_{i}_{j}'] for (i,j) in arcs","position_min":"params['position_min']","position_max":"params['position_max']"},"variables":{"route[i,j]":"Binary for (i,j) in arcs","position[i]":"Integer, position_min <= position[i] <= position_max"},"constraints":["sum(route[i,j] for j != i) == 1 for each i","sum(route[i,j] for i != j) == 1 for each j","position[0] == 0","position[j] >= position[i] + 1 - (position_max-position_min+1)*(1-route[i,j]) for each (i,j) in arcs with j != 0"],"objective":"minimize sum(distance[i,j]*route[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = params["n_cities"]
    position_min = params["position_min"]
    position_max = params["position_max"]

    cities = list(range(n_cities))
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]
    distances = {
        (origin, destination): params[f"dist_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.distance = pyo.Param(
        model.arcs, initialize=distances, within=pyo.Reals
    )
    model.position_lower = pyo.Param(initialize=position_min)
    model.position_upper = pyo.Param(initialize=position_max)

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(model.position_lower, model.position_upper),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.outgoing_routes = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_routes = pyo.Constraint(
        model.cities, rule=incoming_rule
    )
    model.depot_position = pyo.Constraint(expr=model.position[0] == 0)

    def subtour_rule(instance, origin, destination):
        # The return arc to City 0 closes the tour without increasing position.
        if destination == 0:
            return pyo.Constraint.Skip
        big_m = instance.position_upper - instance.position_lower + 1
        return instance.position[destination] >= (
            instance.position[origin]
            + 1
            - big_m * (1 - instance.route[origin, destination])
        )

    model.subtour_elimination = pyo.Constraint(
        model.arcs, rule=subtour_rule
    )
    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[origin, destination]
            * model.route[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when automatic solution loading cannot
        # retrieve a feasible solution. Unexpected solver errors propagate.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no feasible solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}