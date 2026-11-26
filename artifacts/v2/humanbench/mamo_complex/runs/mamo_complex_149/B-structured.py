# IR: {"sets":{"cities":"0..4","arcs":"(i,j) in cities^2 with i != j","subsets":"all city subsets S with 2 <= |S| <= 4"},"params":{"cost_matrix":"5x5 matrix read from params['cost_matrix']"},"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each i: sum(x[i,j] for j != i) == 1","For each j: sum(x[i,j] for i != j) == 1","For each S in subsets: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":"minimize sum(cost_matrix[i][j] * x[i,j] for (i,j) in arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 4)
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
        initialize={
            (i, j): cost_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.outgoing_constraints = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_constraints = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    cities = tuple(model.cities)
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_constraints.add(
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}