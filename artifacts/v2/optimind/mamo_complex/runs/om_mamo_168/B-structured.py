# IR: {"sets":{"V":["E","F","G","H","I"],"A":"{(i,j) in V x V: i != j}","S":"{S subset V: 2 <= |S| <= 4}"},"params":{"cost_E_to_F":"real","cost_E_to_G":"real","cost_E_to_H":"real","cost_E_to_I":"real","cost_F_to_E":"real","cost_F_to_G":"real","cost_F_to_H":"real","cost_F_to_I":"real","cost_G_to_E":"real","cost_G_to_F":"real","cost_G_to_H":"real","cost_G_to_I":"real","cost_H_to_E":"real","cost_H_to_F":"real","cost_H_to_G":"real","cost_H_to_I":"real","cost_I_to_E":"real","cost_I_to_F":"real","cost_I_to_G":"real","cost_I_to_H":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","sum(x[i,j] for i in S for j in S if i != j) <= |S|-1 for S in S"],"objective":"minimize sum(cost_i_to_j * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ("E", "F", "G", "H", "I")
    arcs = tuple(
        (origin, destination)
        for origin in locations
        for destination in locations
        if origin != destination
    )
    costs = {
        ("E", "F"): params["cost_E_to_F"],
        ("E", "G"): params["cost_E_to_G"],
        ("E", "H"): params["cost_E_to_H"],
        ("E", "I"): params["cost_E_to_I"],
        ("F", "E"): params["cost_F_to_E"],
        ("F", "G"): params["cost_F_to_G"],
        ("F", "H"): params["cost_F_to_H"],
        ("F", "I"): params["cost_F_to_I"],
        ("G", "E"): params["cost_G_to_E"],
        ("G", "F"): params["cost_G_to_F"],
        ("G", "H"): params["cost_G_to_H"],
        ("G", "I"): params["cost_G_to_I"],
        ("H", "E"): params["cost_H_to_E"],
        ("H", "F"): params["cost_H_to_F"],
        ("H", "G"): params["cost_H_to_G"],
        ("H", "I"): params["cost_H_to_I"],
        ("I", "E"): params["cost_I_to_E"],
        ("I", "F"): params["cost_I_to_F"],
        ("I", "G"): params["cost_I_to_G"],
        ("I", "H"): params["cost_I_to_H"],
    }

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.locations
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.locations
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.locations, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.locations, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(locations)):
        for subset in combinations(locations, subset_size):
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
            model.delivery_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPSI raises this when it cannot load a feasible solution.
        # Unexpected solver errors must propagate.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}