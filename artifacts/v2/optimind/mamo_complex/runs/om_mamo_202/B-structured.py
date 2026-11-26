# IR: {"sets":{"N":"{1,...,6}","A":"{(i,j) in N x N: i != j}","S":"{U subset N: 2 <= |U| <= 5}"},"params":{"c[i,j]":"params[f'c{i}{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for each i in N","sum(x[i,j] for i in N if i != j) = 1 for each j in N","sum(x[i,j] for i in U for j in U if i != j) <= |U|-1 for each U in S"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

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
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    )

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"c{origin}{destination}"]
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
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}