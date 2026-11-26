# IR: {"sets":{"areas":["A","B","C","D","E","F","G","H","I","J","K","L"],"covers":{"A":["A","C","E","G","H","I"],"B":["B","H","I"],"C":["A","C","G","H","I"],"D":["D","J"],"E":["A","E","G"],"F":["F","J","K"],"G":["A","C","E","G"],"H":["A","B","C","H","I"],"I":["A","B","C","H","I"],"J":["D","F","J","K","L"],"K":["F","J","K","L"],"L":["J","K","L"]}},"params":{"coverage_radius_m":{"source":"params[\"coverage_radius_m\"]","domain":"nonnegative real","role":"radius associated with the supplied coverage topology"}},"variables":{"build[site]":"binary"},"constraints":["For each area: sum(build[site] for site in areas if area in covers[site]) >= 1."],"objective":"minimize sum(build[site] for site in areas)"}
#
# The table supplies coverage relationships, not pairwise distances.
# Its topology is therefore treated as valid for the supplied radius.
# Changing the radius alone cannot determine a different coverage topology.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage_radius_m = params["coverage_radius_m"]

    areas = tuple("ABCDEFGHIJKL")
    covers = {
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
    model.coverage_radius_m = pyo.Param(
        initialize=coverage_radius_m,
        within=pyo.NonNegativeReals,
    )
    model.covers = pyo.Set(
        model.areas,
        within=model.areas,
        initialize=covers,
    )
    model.build = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return sum(
            instance.build[site]
            for site in instance.areas
            if area in instance.covers[site]
        ) >= 1

    model.coverage_requirement = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )
    model.total_stores = pyo.Objective(
        expr=sum(model.build[site] for site in model.areas),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_stores))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}