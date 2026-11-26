# IR: {"sets":{"cities":["E","F","G","H","I"],"arcs":"ordered pairs of distinct cities","subsets":"city subsets with sizes 2 through 4"},"params":{"cost_E_F":"real","cost_E_G":"real","cost_E_H":"real","cost_E_I":"real","cost_F_E":"real","cost_F_G":"real","cost_F_H":"real","cost_F_I":"real","cost_G_E":"real","cost_G_F":"real","cost_G_H":"real","cost_G_I":"real","cost_H_E":"real","cost_H_F":"real","cost_H_G":"real","cost_H_I":"real","cost_I_E":"real","cost_I_F":"real","cost_I_G":"real","cost_I_H":"real"},"variables":{"x[i,j]":"binary for each arc"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1.","For each city j: sum(x[i,j] for i != j) = 1.","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S| - 1."],"objective":"minimize sum(cost[i,j] * x[i,j] for each arc)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    costs = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("E", "I"): params["cost_E_I"],
        ("F", "E"): params["cost_F_E"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("F", "I"): params["cost_F_I"],
        ("G", "E"): params["cost_G_E"],
        ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"],
        ("G", "I"): params["cost_G_I"],
        ("H", "E"): params["cost_H_E"],
        ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"],
        ("H", "I"): params["cost_H_I"],
        ("I", "E"): params["cost_I_E"],
        ("I", "F"): params["cost_I_F"],
        ("I", "G"): params["cost_I_G"],
        ("I", "H"): params["cost_I_H"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(model.arcs, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in model.cities
            if destination != origin
        ) == 1

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in model.cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
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
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}