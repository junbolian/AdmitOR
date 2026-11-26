# IR: {"sets":{"V":[1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 4}"},"params":{"cost":"cost[i,j] = params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["For every i in V: sum(x[i,j] for j in V if j != i) = 1","For every j in V: sum(x[i,j] for i in V if i != j) = 1","For every T in S: sum(x[i,j] for i,j in T if i != j) <= |T|-1"],"objective":"Minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shops = (1, 2, 3, 4, 5)
    arcs = [(i, j) for i in shops for j in shops if i != j]
    costs = {(i, j): params[f"cost_{i}_{j}"] for i, j in arcs}

    model = pyo.ConcreteModel()
    model.shops = pyo.Set(initialize=shops, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.shops if j != i) == 1

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.shops if i != j) == 1

    model.outgoing = pyo.Constraint(model.shops, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.shops, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(shops)):
        for subset in combinations(shops, subset_size):
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
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}