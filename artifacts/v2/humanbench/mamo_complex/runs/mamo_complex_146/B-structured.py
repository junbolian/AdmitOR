# IR: {"sets":{"cities":["Alpha","Bravo","Charlie","Delta"],"arcs":"all ordered pairs of distinct cities","subsets":"all city subsets of size 2 or 3"},"params":["cost_Alpha_Bravo","cost_Alpha_Charlie","cost_Alpha_Delta","cost_Bravo_Alpha","cost_Bravo_Charlie","cost_Bravo_Delta","cost_Charlie_Alpha","cost_Charlie_Bravo","cost_Charlie_Delta","cost_Delta_Alpha","cost_Delta_Bravo","cost_Delta_Charlie"],"variables":{"route[i,j]":{"type":"binary","index":"arcs"}},"constraints":["For each city i: sum(route[i,j] for j != i) == 1","For each city j: sum(route[i,j] for i != j) == 1","For each subset S: sum(route[i,j] for i,j in S with i != j) <= len(S)-1"],"objective":"minimize sum(cost_i_j * route[i,j] for (i,j) in arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("Alpha", "Bravo", "Charlie", "Delta")
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]

    costs = {
        ("Alpha", "Bravo"): params["cost_Alpha_Bravo"],
        ("Alpha", "Charlie"): params["cost_Alpha_Charlie"],
        ("Alpha", "Delta"): params["cost_Alpha_Delta"],
        ("Bravo", "Alpha"): params["cost_Bravo_Alpha"],
        ("Bravo", "Charlie"): params["cost_Bravo_Charlie"],
        ("Bravo", "Delta"): params["cost_Bravo_Delta"],
        ("Charlie", "Alpha"): params["cost_Charlie_Alpha"],
        ("Charlie", "Bravo"): params["cost_Charlie_Bravo"],
        ("Charlie", "Delta"): params["cost_Charlie_Delta"],
        ("Delta", "Alpha"): params["cost_Delta_Alpha"],
        ("Delta", "Bravo"): params["cost_Delta_Bravo"],
        ("Delta", "Charlie"): params["cost_Delta_Charlie"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.route = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.outgoing_once = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_once = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
                sum(
                    model.route[origin, destination]
                    for origin in subset
                    for destination in subset
                    if origin != destination
                )
                <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.delivery_cost[origin, destination]
            * model.route[origin, destination]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}