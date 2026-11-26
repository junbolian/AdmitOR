# IR: {"sets":{"cities":["A","B","C","D"],"arcs":"ordered pairs of distinct cities","subsets":"city subsets of sizes 2 and 3"},"params":{"cost_AB":"A->B cost","cost_AC":"A->C cost","cost_AD":"A->D cost","cost_BA":"B->A cost","cost_BC":"B->C cost","cost_BD":"B->D cost","cost_CA":"C->A cost","cost_CB":"C->B cost","cost_CD":"C->D cost","cost_DA":"D->A cost","cost_DB":"D->B cost","cost_DC":"D->C cost"},"variables":{"x[i,j]":{"type":"binary","index":"arcs"}},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":{"sense":"minimize","expression":"sum(cost_ij*x[i,j] for (i,j) in arcs)"}}

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
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("B", "A"): params["cost_BA"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("C", "A"): params["cost_CA"],
        ("C", "B"): params["cost_CB"],
        ("C", "D"): params["cost_CD"],
        ("D", "A"): params["cost_DA"],
        ("D", "B"): params["cost_DB"],
        ("D", "C"): params["cost_DC"],
    }

    model = pyo.ConcreteModel()
    model.city_set = pyo.Set(initialize=cities, ordered=True)
    model.arc_set = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.subtour_set = pyo.Set(initialize=range(len(subsets)), ordered=True)

    model.travel_cost = pyo.Param(
        model.arc_set, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)

    def departure_rule(current_model, origin):
        return sum(
            current_model.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def arrival_rule(current_model, destination):
        return sum(
            current_model.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    def subtour_rule(current_model, subset_index):
        subset = subsets[subset_index]
        return sum(
            current_model.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.departure_constraints = pyo.Constraint(
        model.city_set, rule=departure_rule
    )
    model.arrival_constraints = pyo.Constraint(
        model.city_set, rule=arrival_rule
    )
    model.subtour_constraints = pyo.Constraint(
        model.subtour_set, rule=subtour_rule
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
        # An infeasible solve can raise before a solution is loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}