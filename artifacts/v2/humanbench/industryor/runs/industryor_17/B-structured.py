# IR: {"sets":{"areas":["A","B","C","D","E","F","G","H","I","J","K","L"],"coverage":{"A":["A","C","E","G","H","I"],"B":["B","H","I"],"C":["A","C","G","H","I"],"D":["D","J"],"E":["A","E","G"],"F":["F","J","K"],"G":["A","C","E","G"],"H":["A","B","C","H","I"],"I":["A","B","C","H","I"],"J":["D","F","J","K","L"],"K":["F","J","K","L"],"L":["J","K","L"]}},"params":{"coverage_radius":"nonnegative distance read from params; supplied coverage sets encode reachability at this radius"},"variables":{"open_store[area]":"binary"},"constraints":["For every residential area a: sum(open_store[s] for s in coverage[a]) >= 1"],"objective":"minimize sum(open_store[s] for s in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Only coverage sets, not pairwise distances, are supplied. These sets
    # are therefore treated as precomputed for params["coverage_radius"].
    # A different radius requires correspondingly updated coverage data.
    coverage_radius = params["coverage_radius"]

    areas = tuple("ABCDEFGHIJKL")
    coverage = {
        "A": ("A", "C", "E", "G", "H", "I"),
        "B": ("B", "H", "I"),
        "C": ("A", "C", "G", "H", "I"),
        "D": ("D", "J"),
        "E": ("A", "E", "G"),
        "F": ("F", "J", "K"),
        "G": ("A", "C", "E", "G"),
        "H": ("A", "B", "C", "H", "I"),
        "I": ("A", "B", "C", "H", "I"),
        "J": ("D", "F", "J", "K", "L"),
        "K": ("F", "J", "K", "L"),
        "L": ("J", "K", "L"),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.Set(initialize=areas, ordered=True)
    model.coverage_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.coverage = pyo.Set(
        model.areas,
        initialize=coverage,
        within=model.areas,
    )
    model.open_store = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return sum(
            instance.open_store[site]
            for site in instance.coverage[area]
        ) >= 1

    model.coverage_requirement = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )
    model.total_stores = pyo.Objective(
        expr=sum(model.open_store[site] for site in model.areas),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_stores))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}