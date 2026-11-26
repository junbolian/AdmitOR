# IR: {"sets":{"V":["E","F","G","H"],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 3}"},"params":{"cost_E_to_F":"real","cost_E_to_G":"real","cost_E_to_H":"real","cost_F_to_E":"real","cost_F_to_G":"real","cost_F_to_H":"real","cost_G_to_E":"real","cost_G_to_F":"real","cost_G_to_H":"real","cost_H_to_E":"real","cost_H_to_F":"real","cost_H_to_G":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for each i in V","sum(x[i,j] for i in V if i != j) = 1 for each j in V","sum(x[i,j] for i,j in T if i != j) <= |T|-1 for each T in S"],"objective":"minimize sum(cost_i_to_j * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ("E", "F", "G", "H")
    arcs = [
        (origin, destination)
        for origin in locations
        for destination in locations
        if origin != destination
    ]
    subsets = [
        subset
        for size in range(2, len(locations))
        for subset in combinations(locations, size)
    ]
    costs = {
        (origin, destination): params[f"cost_{origin}_to_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.subset_ids = pyo.RangeSet(0, len(subsets) - 1)

    model.delivery_cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )
    model.route = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.locations
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.locations
            if origin != destination
        ) == 1

    def subtour_rule(instance, subset_id):
        subset = subsets[subset_id]
        return sum(
            instance.route[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.outgoing_constraints = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )
    model.incoming_constraints = pyo.Constraint(
        model.locations, rule=incoming_rule
    )
    model.subtour_constraints = pyo.Constraint(
        model.subset_ids, rule=subtour_rule
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}