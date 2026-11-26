# IR: {"sets":{"cities":["A","B","C","D"],"arcs":"ordered pairs of distinct cities","subsets":"city subsets of sizes 2 and 3"},"params":["cost_A_B","cost_A_C","cost_A_D","cost_B_A","cost_B_C","cost_B_D","cost_C_A","cost_C_B","cost_C_D","cost_D_A","cost_D_B","cost_D_C"],"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for all arcs)"}

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
    subsets = tuple(
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
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

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_cuts = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_cuts.add(
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
            for origin, destination in arcs
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