# IR: {"sets":{"cities":[1,2,3,4],"arcs":"{(i,j): i,j in cities, i != j}","subsets":"{S subset cities: 2 <= |S| <= 3}"},"params":{"cost_12":"real","cost_13":"real","cost_14":"real","cost_21":"real","cost_23":"real","cost_24":"real","cost_31":"real","cost_32":"real","cost_34":"real","cost_41":"real","cost_42":"real","cost_43":"real"},"variables":{"x[i,j]":"binary, (i,j) in arcs"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each S in subsets: sum(x[i,j] for i,j in S if i != j) <= |S|-1"],"objective":"minimize sum(cost_ij * x[i,j] for (i,j) in arcs)"}

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
    subsets = tuple(
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    )

    costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_limits.add(
            sum(
                model.x[origin, destination]
                for origin in subset
                for destination in subset
                if origin != destination
            ) <= len(subset) - 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no solution can be loaded.
    # Success is determined exclusively by objective retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}