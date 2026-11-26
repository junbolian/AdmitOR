# IR: {"sets":{"V":[1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 4}"},"params":{"cost[i,j]":"params['cost_' + str(i) + '_' + str(j)] for each (i,j) in A"},"variables":{"x[i,j]":"binary for each (i,j) in A"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each T in S: sum(x[i,j] for i in T for j in T if i != j) <= |T| - 1"],"objective":"minimize sum(cost[i,j] * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=[1, 2, 3, 4, 5], ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.V
            for destination in model.V
            if origin != destination
        ],
    )

    model.cost = pyo.Param(
        model.A,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def outgoing_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in problem.V
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)

    def incoming_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in problem.V
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(model.V)):
        for subset in combinations(model.V, subset_size):
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
            model.cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}