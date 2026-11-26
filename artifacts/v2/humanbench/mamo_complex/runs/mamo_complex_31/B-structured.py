# IR: {"sets":{"C":[1,2,3,4,5],"A":"{(i,j) in C x C : i != j}","S":"{S subset C : 2 <= |S| <= 4}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in C: sum(x[i,j] for j in C if j != i) = 1","For each j in C: sum(x[i,j] for i in C if i != j) = 1","For each S: sum(x[i,j] for i,j in S if i != j) <= |S| - 1"],"objective":"minimize sum(cost[i,j] * x[i,j] for (i,j) in A)"}

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
    subsets = tuple(
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
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

    model.departure = pyo.Constraint(model.cities, rule=departure_rule)
    model.arrival = pyo.Constraint(model.cities, rule=arrival_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_elimination.add(
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
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}