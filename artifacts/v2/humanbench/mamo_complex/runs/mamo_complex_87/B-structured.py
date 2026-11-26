# IR: {"sets":{"V":["E","F","G","H","I"],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| < |V|}"},"params":["cost_E_F","cost_E_G","cost_E_H","cost_E_I","cost_F_E","cost_F_G","cost_F_H","cost_F_I","cost_G_E","cost_G_F","cost_G_H","cost_G_I","cost_H_E","cost_H_F","cost_H_G","cost_H_I","cost_I_E","cost_I_F","cost_I_G","cost_I_H"],"decision_variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) == 1","For each j in V: sum(x[i,j] for i in V if i != j) == 1","For each T in S: sum(x[i,j] for i,j in T if i != j) <= |T|-1"],"objective":"Minimize sum(cost_i_j * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ("E", "F", "G", "H", "I")
    arcs = [(origin, destination)
            for origin in locations
            for destination in locations
            if origin != destination]

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

    model.outgoing_constraints = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )
    model.incoming_constraints = pyo.Constraint(
        model.locations, rule=incoming_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(locations)):
        for subset in combinations(locations, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.x[origin, destination]
                    for origin in subset
                    for destination in subset
                    if origin != destination
                ) <= len(subset) - 1
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
    except RuntimeError as exc:
        # HiGHS raises this when no feasible solution can be loaded.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}