# IR: {"sets":{"V":"1..n_cities","A":"{(i,j) in V x V: i != j}","U":"V \\ {1}"},"params":{"n_cities":"params['n_cities']","d[i,j]":"params['distance_matrix'][i-1][j-1]"},"variables":{"x[i,j]":"Binary, (i,j) in A","u[i]":"Real in [1,n_cities-1], i in U"},"constraints":{"outgoing[i]":"sum(x[i,j] for j in V if j != i) = 1","incoming[j]":"sum(x[i,j] for i in V if i != j) = 1","subtour[i,j]":"u[i]-u[j]+n_cities*x[i,j] <= n_cities-1, i,j in U, i != j"},"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = params["n_cities"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(
        initialize=range(1, n_cities + 1), ordered=True
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.nonroot_cities = pyo.Set(
        initialize=range(2, n_cities + 1), ordered=True
    )

    model.distances = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distance_matrix[i - 1][j - 1]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.nonroot_cities,
        domain=pyo.Reals,
        bounds=(1, n_cities - 1),
    )

    def outgoing_rule(block, i):
        return sum(
            block.x[i, j] for j in block.cities if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )

    def incoming_rule(block, j):
        return sum(
            block.x[i, j] for i in block.cities if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    def subtour_rule(block, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            block.u[i] - block.u[j] + n_cities * block.x[i, j]
            <= n_cities - 1
        )

    model.subtour = pyo.Constraint(
        model.nonroot_cities,
        model.nonroot_cities,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distances[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}