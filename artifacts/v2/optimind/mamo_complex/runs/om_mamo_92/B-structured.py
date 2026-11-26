# IR: {"sets":{"cities":["A","B","C","D"],"arcs":"all ordered pairs of distinct cities","subsets":"all city subsets S with 2 <= |S| <= 3"},"params":["cost_A_B","cost_A_C","cost_A_D","cost_B_A","cost_B_C","cost_B_D","cost_C_A","cost_C_B","cost_C_D","cost_D_A","cost_D_B","cost_D_C"],"variables":{"x[i,j]":{"type":"binary","index":"arcs"}},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":{"sense":"minimize","expression":"sum(cost_i_j * x[i,j] for (i,j) in arcs)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("A", "B", "C", "D")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    costs = {
        ("A", "B"): params["cost_A_B"],
        ("A", "C"): params["cost_A_C"],
        ("A", "D"): params["cost_A_D"],
        ("B", "A"): params["cost_B_A"],
        ("B", "C"): params["cost_B_C"],
        ("B", "D"): params["cost_B_D"],
        ("C", "A"): params["cost_C_A"],
        ("C", "B"): params["cost_C_B"],
        ("C", "D"): params["cost_C_D"],
        ("D", "A"): params["cost_D_A"],
        ("D", "B"): params["cost_D_B"],
        ("D", "C"): params["cost_D_C"],
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
            for destination in cities
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_constraints.add(
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
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions must propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}