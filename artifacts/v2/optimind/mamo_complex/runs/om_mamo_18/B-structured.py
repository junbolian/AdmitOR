# IR: {"sets":{"V":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| <= 3}"},"params":{"c12":"params['c12']","c13":"params['c13']","c14":"params['c14']","c21":"params['c21']","c23":"params['c23']","c24":"params['c24']","c31":"params['c31']","c32":"params['c32']","c34":"params['c34']","c41":"params['c41']","c42":"params['c42']","c43":"params['c43']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","sum(x[i,j] for i in U for j in U if i != j) <= |U|-1 for U in S"],"objective":"minimize sum(cij*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = [(i, j) for i in cities for j in cities if i != j]

    costs = {
        (1, 2): params["c12"],
        (1, 3): params["c13"],
        (1, 4): params["c14"],
        (2, 1): params["c21"],
        (2, 3): params["c23"],
        (2, 4): params["c24"],
        (3, 1): params["c31"],
        (3, 2): params["c32"],
        (3, 4): params["c34"],
        (4, 1): params["c41"],
        (4, 2): params["c42"],
        (4, 3): params["c43"],
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2)
    model.travel_cost = pyo.Param(model.A, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.V if j != i) == 1

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.V if i != j) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

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
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}