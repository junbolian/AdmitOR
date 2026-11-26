# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j): i,j in V, i != j}","S":"{S subset V: 2 <= |S| <= 5}"},"params":{"cost_matrix":"6x6 matrix supplied by params['cost_matrix']","c[i,j]":"cost_matrix[i-1][j-1] for (i,j) in A"},"variables":{"x[i,j]":{"type":"binary","indices":"A"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each S: sum(x[i,j] for i,j in S if i != j) <= |S|-1"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize=lambda _, i, j: cost_matrix[i - 1][j - 1],
        within=pyo.Reals,
    )
    model.route = pyo.Var(model.arcs, domain=pyo.Binary)

    def departure_rule(_, i):
        return sum(
            model.route[i, j] for j in model.cities if j != i
        ) == 1

    def arrival_rule(_, j):
        return sum(
            model.route[i, j] for i in model.cities if i != j
        ) == 1

    model.departures = pyo.Constraint(model.cities, rule=departure_rule)
    model.arrivals = pyo.Constraint(model.cities, rule=arrival_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, 6):
        for subset in combinations(model.cities, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.route[i, j]
                    for i in subset
                    for j in subset
                    if i != j
                )
                <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}