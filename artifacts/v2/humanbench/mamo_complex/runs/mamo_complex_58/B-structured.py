# IR: {"sets":{"V":"{0,...,5}","A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| <= 5}"},"params":{"cost":"params['cost'], indexed by zero-based city pairs"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For each U in S: sum(x[i,j] for i,j in U with i != j) <= |U|-1"],"objective":"minimize sum(cost[i][j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(6)
            for j in range(6)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.cities if j != i
        ) == 1

    def incoming_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.cities if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, 6):
        for subset in combinations(range(6), subset_size):
            model.subtour_elimination.add(
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

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}