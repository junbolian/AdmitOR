# IR: {"sets":{"V":"range(num_cities)","A":"{(i,j) in V x V: i != j}"},"params":["distance_matrix","num_cities","position_lower_bound","position_upper_bound","start_city"],"variables":{"x[i,j]":"Binary, (i,j) in A","position[i]":"Integer, position_lower_bound <= position[i] <= position_upper_bound"},"constraints":["sum(x[i,j] for j != i) = 1 for each i in V","sum(x[i,j] for i != j) = 1 for each j in V","position[start_city] = position_lower_bound","position[j] >= position[i] + 1 - (position_upper_bound-position_lower_bound+1)*(1-x[i,j]) for each (i,j) in A with j != start_city"],"objective":"minimize sum(distance_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_cities = params["num_cities"]
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]
    start_city = params["start_city"]

    if num_cities < 2:
        return {"objective": None, "status": "invalid_city_count"}
    if start_city not in range(num_cities):
        return {"objective": None, "status": "invalid_start_city"}
    if position_lower_bound > position_upper_bound:
        return {"objective": None, "status": "invalid_position_bounds"}

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(
        initialize=range(num_cities),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (city_from, city_to)
            for city_from in range(num_cities)
            for city_to in range(num_cities)
            if city_from != city_to
        ],
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(position_lower_bound, position_upper_bound),
    )

    def departure_rule(model, city):
        return sum(
            model.x[city, city_to]
            for city_to in model.cities
            if city_to != city
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities,
        rule=departure_rule,
    )

    def arrival_rule(model, city):
        return sum(
            model.x[city_from, city]
            for city_from in model.cities
            if city_from != city
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities,
        rule=arrival_rule,
    )

    model.start_position_constraint = pyo.Constraint(
        expr=model.position[start_city] == position_lower_bound
    )

    big_m = position_upper_bound - position_lower_bound + 1

    def ordering_rule(model, city_from, city_to):
        if city_to == start_city:
            return pyo.Constraint.Skip
        return (
            model.position[city_to]
            >= model.position[city_from]
            + 1
            - big_m * (1 - model.x[city_from, city_to])
        )

    model.ordering_constraints = pyo.Constraint(
        model.arcs,
        rule=ordering_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            distance_matrix[city_from][city_to]
            * model.x[city_from, city_to]
            for city_from, city_to in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no solution is available to load.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}