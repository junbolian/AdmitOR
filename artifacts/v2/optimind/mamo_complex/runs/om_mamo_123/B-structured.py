# IR: {"sets":{"N":[1,2,3,4,5],"A":"{(i,j) in N x N: i != j}","S":"{U subset N: 2 <= |U| <= 4}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["For each i in N: sum(x[i,j] for j in N if j != i) = 1","For each j in N: sum(x[i,j] for i in N if i != j) = 1","For each U in S: sum(x[i,j] for i in U for j in U if i != j) <= |U| - 1"],"objective":"Minimize sum(cost[i,j] * x[i,j] for (i,j) in A)"}

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
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

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
            model.travel_cost[origin, destination] * model.x[origin, destination]
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