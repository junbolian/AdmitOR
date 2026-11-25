# IR: {"sets":{"V":"range(num_cities)","N":"V excluding 0","A":"[(i,j) for i in V for j in V if i!=j]"},"params":{"num_cities":"params['num_cities']","position_lower":"params['position_lower']","position_upper":"params['position_upper']","cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [position_lower,position_upper] for i in V"},"constraints":["sum(x[i,j] for j in V if j!=i)=1 for i in V","sum(x[i,j] for i in V if i!=j)=1 for j in V","u[0]=position_lower","u[i]>=position_lower+1 for i in N","u[i]-u[j]+num_cities*x[i,j]<=num_cities-1 for i,j in N with i!=j"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.city_count = pyo.Param(
        initialize=params["num_cities"],
        within=pyo.PositiveIntegers,
    )
    model.position_min = pyo.Param(
        initialize=params["position_lower"],
        within=pyo.Reals,
    )
    model.position_max = pyo.Param(
        initialize=params["position_upper"],
        within=pyo.Reals,
    )

    city_count = int(pyo.value(model.city_count))
    cities = range(city_count)

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.non_depot_cities = pyo.Set(
        initialize=[city for city in cities if city != 0],
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in cities
            for destination in cities
            if origin != destination
        ],
        ordered=True,
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.tour_position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=(
            pyo.value(model.position_min),
            pyo.value(model.position_max),
        ),
    )

    def departure_rule(instance, origin):
        return sum(
            instance.route_arc[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities,
        rule=departure_rule,
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.route_arc[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities,
        rule=arrival_rule,
    )

    model.depot_position_constraint = pyo.Constraint(
        expr=model.tour_position[0] == model.position_min
    )

    def non_depot_position_rule(instance, city):
        return instance.tour_position[city] >= instance.position_min + 1

    model.non_depot_position_constraints = pyo.Constraint(
        model.non_depot_cities,
        rule=non_depot_position_rule,
    )

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.tour_position[origin]
            - instance.tour_position[destination]
            + instance.city_count * instance.route_arc[origin, destination]
            <= instance.city_count - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.non_depot_cities,
        model.non_depot_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}