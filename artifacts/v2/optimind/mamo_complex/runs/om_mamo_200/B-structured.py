# IR: {"sets":{"V":"{1,2,3,4,5}","A":"{(i,j) in V x V: i != j}","S":"all subsets of V with 2 <= size <= 4"},"params":{"cost_matrix":"5x5 matrix from params['cost_matrix']; row i-1, column j-1 gives cost(i,j)"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For each subset T in S: sum(x[i,j] for i,j in T with i != j) <= size(T)-1"],"objective":"Minimize sum(cost_matrix[i-1][j-1]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
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
            (origin, destination): cost_matrix[origin - 1][destination - 1]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(block, origin):
        return sum(
            block.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(block, destination):
        return sum(
            block.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing_constraints = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_constraints = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_constraints.add(
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
            for origin, destination in arcs
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