# IR: {"sets":{"V":"{1,...,num_cities}, frozen at four cities","A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| < num_cities}"},"params":{"num_cities":"params['num_cities']","cost[i,j]":"params['cost_i_j'] for every (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":{"outgoing":"sum(x[i,j] for j != i) = 1 for each i in V","incoming":"sum(x[i,j] for i != j) = 1 for each j in V","subtour":"sum(x[i,j] for distinct i,j in U) <= |U|-1 for each U in S"},"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    if num_cities != 4:
        raise ValueError("num_cities must equal the frozen index-set size of four.")

    cities = tuple(range(1, int(num_cities) + 1))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    subsets = tuple(
        subset
        for subset_size in range(2, int(num_cities))
        for subset in combinations(cities, subset_size)
    )

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

    model.subtour = pyo.ConstraintList()
    for subset in subsets:
        model.subtour.add(
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}