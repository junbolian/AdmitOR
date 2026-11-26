# IR: {"sets":{"cities":["A","B","C","D","E"],"arcs":"all ordered pairs of distinct cities","subsets":"all city subsets with size 2 through 4"},"params":{"cost_A_to_B":"real","cost_A_to_C":"real","cost_A_to_D":"real","cost_A_to_E":"real","cost_B_to_A":"real","cost_B_to_C":"real","cost_B_to_D":"real","cost_B_to_E":"real","cost_C_to_A":"real","cost_C_to_B":"real","cost_C_to_D":"real","cost_C_to_E":"real","cost_D_to_A":"real","cost_D_to_B":"real","cost_D_to_C":"real","cost_D_to_E":"real","cost_E_to_A":"real","cost_E_to_B":"real","cost_E_to_C":"real","cost_E_to_D":"real"},"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1.","For each city j: sum(x[i,j] for i != j) = 1.","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1."],"objective":"minimize sum(cost_i_to_j * x[i,j] for all arcs (i,j))"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("A", "B", "C", "D", "E")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    travel_costs = {
        ("A", "B"): params["cost_A_to_B"],
        ("A", "C"): params["cost_A_to_C"],
        ("A", "D"): params["cost_A_to_D"],
        ("A", "E"): params["cost_A_to_E"],
        ("B", "A"): params["cost_B_to_A"],
        ("B", "C"): params["cost_B_to_C"],
        ("B", "D"): params["cost_B_to_D"],
        ("B", "E"): params["cost_B_to_E"],
        ("C", "A"): params["cost_C_to_A"],
        ("C", "B"): params["cost_C_to_B"],
        ("C", "D"): params["cost_C_to_D"],
        ("C", "E"): params["cost_C_to_E"],
        ("D", "A"): params["cost_D_to_A"],
        ("D", "B"): params["cost_D_to_B"],
        ("D", "C"): params["cost_D_to_C"],
        ("D", "E"): params["cost_D_to_E"],
        ("E", "A"): params["cost_E_to_A"],
        ("E", "B"): params["cost_E_to_B"],
        ("E", "C"): params["cost_E_to_C"],
        ("E", "D"): params["cost_E_to_D"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=travel_costs, within=pyo.Reals
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave unexpected solver exceptions visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}