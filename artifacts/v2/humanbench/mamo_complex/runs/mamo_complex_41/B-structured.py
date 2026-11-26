# IR: {"sets":{"C":["E","F","G","H","I"],"A":"{(i,j) in C x C: i != j}","S":"{T subset C: 2 <= |T| < |C|}"},"params":{"cost_EF":"real","cost_EG":"real","cost_EH":"real","cost_EI":"real","cost_FE":"real","cost_FG":"real","cost_FH":"real","cost_FI":"real","cost_GE":"real","cost_GF":"real","cost_GH":"real","cost_GI":"real","cost_HE":"real","cost_HF":"real","cost_HG":"real","cost_HI":"real","cost_IE":"real","cost_IF":"real","cost_IG":"real","cost_IH":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in C: sum(x[i,j] for j in C if j != i) = 1","For each j in C: sum(x[i,j] for i in C if i != j) = 1","For each T in S: sum(x[i,j] for i,j in T if i != j) <= |T| - 1"],"objective":"minimize sum(cost_ij * x[i,j] for (i,j) in A)"}

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
        ("E", "F"): params["cost_EF"],
        ("E", "G"): params["cost_EG"],
        ("E", "H"): params["cost_EH"],
        ("E", "I"): params["cost_EI"],
        ("F", "E"): params["cost_FE"],
        ("F", "G"): params["cost_FG"],
        ("F", "H"): params["cost_FH"],
        ("F", "I"): params["cost_FI"],
        ("G", "E"): params["cost_GE"],
        ("G", "F"): params["cost_GF"],
        ("G", "H"): params["cost_GH"],
        ("G", "I"): params["cost_GI"],
        ("H", "E"): params["cost_HE"],
        ("H", "F"): params["cost_HF"],
        ("H", "G"): params["cost_HG"],
        ("H", "I"): params["cost_HI"],
        ("I", "E"): params["cost_IE"],
        ("I", "F"): params["cost_IF"],
        ("I", "G"): params["cost_IG"],
        ("I", "H"): params["cost_IH"],
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}