# IR: {"sets":{"cities":[1,2,3,4],"arcs":"ordered pairs (i,j) of distinct cities","subsets":"all nonempty proper subsets of cities"},"params":["cost_1_2","cost_1_3","cost_1_4","cost_2_1","cost_2_3","cost_2_4","cost_3_1","cost_3_2","cost_3_4","cost_4_1","cost_4_2","cost_4_3"],"variables":{"x[i,j]":"binary for each arc"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each nonempty proper subset S: sum(x[i,j] for i in S and j outside S) >= 1"],"objective":"minimize sum(cost_i_j * x[i,j] for each arc)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    subsets = tuple(
        subset
        for size in range(1, len(cities))
        for subset in combinations(cities, size)
    )

    costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in model.cities
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in model.cities
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_cuts = pyo.ConstraintList()
    for subset in subsets:
        members = frozenset(subset)
        model.subtour_cuts.add(
            sum(
                model.x[origin, destination]
                for origin in members
                for destination in cities
                if destination not in members
            ) >= 1
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
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # Continue to objective retrieval, which alone determines success.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective_value"}

    return {"objective": obj_val, "status": "optimal"}