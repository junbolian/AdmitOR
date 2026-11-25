# IR: {"sets":{"V":"range(num_cities)","A":"{(i,j) in V x V: i != j}","R":"V excluding start_city"},"params":{"distance_matrix":"directed travel distances","num_cities":"number of cities","position_lower_bound":"lower bound for every position","position_upper_bound":"upper bound for every position","start_city":"fixed starting and ending city"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [position_lower_bound,position_upper_bound] for i in V"},"constraints":["sum(x[i,j] for j != i) = 1 for each i in V","sum(x[i,j] for i != j) = 1 for each j in V","u[start_city] = 0","u[i] - u[j] + num_cities*x[i,j] <= num_cities - 1 for distinct i,j in R"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_cities = params["num_cities"]
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]
    start_city = params["start_city"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(
        initialize=range(num_cities),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (origin, destination)
            for origin in range(num_cities)
            for destination in range(num_cities)
            if origin != destination
        ),
    )
    model.other_cities = pyo.Set(
        initialize=(
            city for city in range(num_cities) if city != start_city
        ),
        ordered=True,
    )

    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): distance_matrix[origin][destination]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.tour_position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(position_lower_bound, position_upper_bound),
    )

    def departure_rule(current_model, origin):
        return sum(
            current_model.route_arc[origin, destination]
            for destination in current_model.cities
            if destination != origin
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities,
        rule=departure_rule,
    )

    def arrival_rule(current_model, destination):
        return sum(
            current_model.route_arc[origin, destination]
            for origin in current_model.cities
            if origin != destination
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities,
        rule=arrival_rule,
    )

    model.start_position_constraint = pyo.Constraint(
        expr=model.tour_position[start_city] == 0
    )

    def subtour_rule(current_model, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            current_model.tour_position[origin]
            - current_model.tour_position[destination]
            + num_cities * current_model.route_arc[origin, destination]
            <= num_cities - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.other_cities,
        model.other_cities,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this error when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}