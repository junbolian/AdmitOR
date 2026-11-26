# IR: {"sets":{"V":[1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| <= 4}"},"params":{"cost_i_j":"params['cost_i_j'] for every (i,j) in A"},"variables":{"x[i,j]":{"index":"A","type":"binary"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each U in S: sum(x[i,j] for i,j in U if i != j) <= |U| - 1"],"objective":{"sense":"minimize","expression":"sum(cost_i_j * x[i,j] for (i,j) in A)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(1, 6))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
        (4, 5): params["cost_4_5"],
        (5, 1): params["cost_5_1"],
        (5, 2): params["cost_5_2"],
        (5, 3): params["cost_5_3"],
        (5, 4): params["cost_5_4"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.departures = pyo.Constraint(model.cities, rule=departure_rule)
    model.arrivals = pyo.Constraint(model.cities, rule=arrival_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_elimination.add(
                sum(
                    model.x[origin, destination]
                    for origin in subset
                    for destination in subset
                    if origin != destination
                )
                <= subset_size - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}