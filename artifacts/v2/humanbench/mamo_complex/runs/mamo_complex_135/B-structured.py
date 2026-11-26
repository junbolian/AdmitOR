# IR: {"sets":{"N":[1,2,3,4],"A":"{(i,j) in N x N: i != j}","S":"{U subset N: 2 <= |U| <= 3}"},"params":{"c12":"params['c12']","c13":"params['c13']","c14":"params['c14']","c21":"params['c21']","c23":"params['c23']","c24":"params['c24']","c31":"params['c31']","c32":"params['c32']","c34":"params['c34']","c41":"params['c41']","c42":"params['c42']","c43":"params['c43']"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for each i in N","sum(x[i,j] for i in N if i != j) = 1 for each j in N","sum(x[i,j] for i in U for j in U if i != j) <= |U|-1 for each U in S"],"objective":"minimize sum(c_ij*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
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
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def departure_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in model.cities
            if destination != origin
        ) == 1

    def arrival_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in model.cities
            if origin != destination
        ) == 1

    model.departure = pyo.Constraint(model.cities, rule=departure_rule)
    model.arrival = pyo.Constraint(model.cities, rule=arrival_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
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
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}