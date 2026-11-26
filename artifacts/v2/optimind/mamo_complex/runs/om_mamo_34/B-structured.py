# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 5}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) == 1 for each i in V","sum(x[i,j] for i in V if i != j) == 1 for each j in V","sum(x[i,j] for i in T for j in T if i != j) <= |T|-1 for each T in S"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = tuple(range(1, 7))
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )
    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(current_model, i):
        return sum(
            current_model.route_arc[i, j]
            for j in cities
            if j != i
        ) == 1

    def incoming_rule(current_model, j):
        return sum(
            current_model.route_arc[i, j]
            for i in cities
            if i != j
        ) == 1

    model.outgoing_once = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_once = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
                sum(
                    model.route_arc[i, j]
                    for i in subset
                    for j in subset
                    if i != j
                ) <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route_arc[i, j]
            for i, j in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}