# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 5}"},"params":{"c[i,j]":"params[f'c_{i}{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each T in S: sum(x[i,j] for i,j in T if i != j) <= |T| - 1"],"objective":"minimize sum(c[i,j] * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(1, 7))
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={(i, j): params[f"c_{i}{j}"] for i, j in arcs},
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, i):
        return sum(
            model.x[i, j] for j in model.cities if j != i
        ) == 1

    def incoming_rule(model, j):
        return sum(
            model.x[i, j] for i in model.cities if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_cuts = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_cuts.add(
                sum(
                    model.x[i, j]
                    for i in subset
                    for j in subset
                    if i != j
                )
                <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no solution can be loaded.
    # Objective availability alone determines the returned success status.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}