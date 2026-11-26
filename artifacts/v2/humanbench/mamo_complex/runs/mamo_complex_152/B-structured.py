# IR: {"sets":{"cities":[1,2,3,4,5,6],"arcs":"(i,j) in cities x cities with i != j","subsets":"all city subsets S with 2 <= |S| <= 5"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for every arc (i,j)"},"variables":{"x[i,j]":{"type":"binary","index":"arcs"}},"constraints":{"outgoing":"sum(x[i,j] for j != i) = 1 for each city i","incoming":"sum(x[i,j] for i != j) = 1 for each city j","subtour":"sum(x[i,j] for i,j in S with i != j) <= |S|-1 for each S in subsets"},"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in arcs)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    subsets = tuple(
        subset
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(model.arcs, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(current_model, origin):
        return sum(
            current_model.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(current_model, destination):
        return sum(
            current_model.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour = pyo.ConstraintList()
    for subset in subsets:
        model.subtour.add(
            sum(
                model.x[origin, destination]
                for origin in subset
                for destination in subset
                if origin != destination
            )
            <= len(subset) - 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when it cannot load a solution.
        # Still use objective retrieval as the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}