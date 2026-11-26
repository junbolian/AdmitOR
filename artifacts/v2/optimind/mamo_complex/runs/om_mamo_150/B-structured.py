# IR: {"sets":{"V":["E","F","G","H","I"],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| < |V|}"},"params":{"cost[i,j]":"params['cost_' + i + '_' + j] for each (i,j) in A"},"variables":{"x[i,j]":{"type":"Binary","index":"A"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each T in S: sum(x[i,j] for i in T for j in T if i != j) <= |T| - 1"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * x[i,j] for (i,j) in A)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]
    subsets = [
        subset
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    ]
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs)
    model.cost = pyo.Param(model.A, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.V
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.V
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset in subsets:
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}