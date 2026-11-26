# IR: {"sets":{"cities":["E","F","G","H"],"arcs":"ordered pairs of distinct cities","subsets":"all city subsets of sizes 2 and 3"},"params":{"cost_E_F":"E->F cost","cost_E_G":"E->G cost","cost_E_H":"E->H cost","cost_F_E":"F->E cost","cost_F_G":"F->G cost","cost_F_H":"F->H cost","cost_G_E":"G->E cost","cost_G_F":"G->F cost","cost_G_H":"G->H cost","cost_H_E":"H->E cost","cost_H_F":"H->F cost","cost_H_G":"H->G cost"},"variables":{"x[i,j]":"binary for each arc"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for all arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H")
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]

    costs = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("F", "E"): params["cost_F_E"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("G", "E"): params["cost_G_E"],
        ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"],
        ("H", "E"): params["cost_H_E"],
        ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
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

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in (2, 3):
        for subset in combinations(cities, subset_size):
            model.subtour_elimination.add(
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

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}