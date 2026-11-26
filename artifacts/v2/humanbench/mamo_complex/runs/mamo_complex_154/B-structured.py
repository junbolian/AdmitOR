# IR: {"sets":{"V":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","S":"{S subset V: 2 <= |S| <= 3}"},"params":{"c12":"params['c12']","c13":"params['c13']","c14":"params['c14']","c21":"params['c21']","c23":"params['c23']","c24":"params['c24']","c31":"params['c31']","c32":"params['c32']","c34":"params['c34']","c41":"params['c41']","c42":"params['c42']","c43":"params['c43']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for each i in V","sum(x[i,j] for i in V if i != j) = 1 for each j in V","sum(x[i,j] for i in S for j in S if i != j) <= |S|-1 for each S in S"],"objective":"minimize sum(c_ij*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    travel_cost = {
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
    model.cities = pyo.Set(initialize=(1, 2, 3, 4), ordered=True)
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
        model.arcs, initialize=travel_cost, within=pyo.Reals
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

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in (2, 3):
        for subset in combinations(model.cities, subset_size):
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}