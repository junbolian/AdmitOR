# IR: {"sets":{"cities":["A","B","C","D","E"],"arcs":"ordered pairs of distinct cities","subsets":"all city subsets with cardinality 2 through 4"},"params":["cost_A_B","cost_A_C","cost_A_D","cost_A_E","cost_B_A","cost_B_C","cost_B_D","cost_B_E","cost_C_A","cost_C_B","cost_C_D","cost_C_E","cost_D_A","cost_D_B","cost_D_C","cost_D_E","cost_E_A","cost_E_B","cost_E_C","cost_E_D"],"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":"minimize sum(cost_i_j*x[i,j] for all arcs (i,j))"}

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
    subsets = tuple(
        subset
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    costs = {
        ("A", "B"): params["cost_A_B"],
        ("A", "C"): params["cost_A_C"],
        ("A", "D"): params["cost_A_D"],
        ("A", "E"): params["cost_A_E"],
        ("B", "A"): params["cost_B_A"],
        ("B", "C"): params["cost_B_C"],
        ("B", "D"): params["cost_B_D"],
        ("B", "E"): params["cost_B_E"],
        ("C", "A"): params["cost_C_A"],
        ("C", "B"): params["cost_C_B"],
        ("C", "D"): params["cost_C_D"],
        ("C", "E"): params["cost_C_E"],
        ("D", "A"): params["cost_D_A"],
        ("D", "B"): params["cost_D_B"],
        ("D", "C"): params["cost_D_C"],
        ("D", "E"): params["cost_D_E"],
        ("E", "A"): params["cost_E_A"],
        ("E", "B"): params["cost_E_B"],
        ("E", "C"): params["cost_E_C"],
        ("E", "D"): params["cost_E_D"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.subset_ids = pyo.Set(initialize=range(len(subsets)), ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in model.cities
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in model.cities
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    def subtour_rule(model, subset_id):
        subset = subsets[subset_id]
        return sum(
            model.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.subtour_elimination = pyo.Constraint(
        model.subset_ids, rule=subtour_rule
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}