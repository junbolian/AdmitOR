# IR: {"sets":{"V":"{0,...,5}","A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 5}"},"params":{"cost":"params['cost'], a 6x6 directed cost matrix"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":{"outgoing":"sum(x[i,j] for j != i) = 1 for each i in V","incoming":"sum(x[i,j] for i != j) = 1 for each j in V","subtour":"sum(x[i,j] for i,j in T, i != j) <= |T|-1 for each T in S"},"objective":"minimize sum(cost[i][j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in vertices
        for destination in vertices
        if origin != destination
    )
    subsets = tuple(
        subset
        for size in range(2, len(vertices))
        for subset in combinations(vertices, size)
    )

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.subset_ids = pyo.Set(
        initialize=range(len(subsets)), ordered=True
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: params["cost"][origin][destination],
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.vertices
            if destination != origin
        ) == 1

    def incoming_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.vertices
            if origin != destination
        ) == 1

    def subtour_rule(mdl, subset_id):
        subset = subsets[subset_id]
        return sum(
            mdl.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.outgoing = pyo.Constraint(model.vertices, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.vertices, rule=incoming_rule)
    model.subtour = pyo.Constraint(model.subset_ids, rule=subtour_rule)

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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}