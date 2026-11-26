# IR: {"sets":{"V":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","S":"{S subset V: 2 <= |S| <= 3}"},"params":{"distance_12":"arc cost (1,2)","distance_13":"arc cost (1,3)","distance_14":"arc cost (1,4)","distance_21":"arc cost (2,1)","distance_23":"arc cost (2,3)","distance_24":"arc cost (2,4)","distance_31":"arc cost (3,1)","distance_32":"arc cost (3,2)","distance_34":"arc cost (3,4)","distance_41":"arc cost (4,1)","distance_42":"arc cost (4,2)","distance_43":"arc cost (4,3)"},"variables":{"x[i,j]":{"index":"A","type":"binary"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each S in S: sum(x[i,j] for i in S for j in S if i != j) <= |S|-1"],"objective":"minimize sum(distance_ij*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    subsets = [
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    ]

    distances = {
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 1): params["distance_21"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 1): params["distance_31"],
        (3, 2): params["distance_32"],
        (3, 4): params["distance_34"],
        (4, 1): params["distance_41"],
        (4, 2): params["distance_42"],
        (4, 3): params["distance_43"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.distance = pyo.Param(
        model.arcs, initialize=distances, within=pyo.Reals
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

    model.subtour_cuts = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_cuts.add(
            sum(
                model.x[i, j]
                for i in subset
                for j in subset
                if i != j
            ) <= len(subset) - 1
        )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}