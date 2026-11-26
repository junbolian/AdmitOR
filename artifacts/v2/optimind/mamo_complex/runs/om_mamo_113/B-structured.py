# IR: {"sets":{"cities":["A","B","C","D","E"],"arcs":"ordered pairs (i,j) of distinct cities","subsets":"city subsets S with 2 <= |S| <= 4"},"params":["cost_AB","cost_AC","cost_AD","cost_AE","cost_BA","cost_BC","cost_BD","cost_BE","cost_CA","cost_CB","cost_CD","cost_CE","cost_DA","cost_DB","cost_DC","cost_DE","cost_EA","cost_EB","cost_EC","cost_ED"],"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":"minimize sum(cost_ij * x[i,j] for all arcs)"}

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

    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("A", "E"): params["cost_AE"],
        ("B", "A"): params["cost_BA"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("B", "E"): params["cost_BE"],
        ("C", "A"): params["cost_CA"],
        ("C", "B"): params["cost_CB"],
        ("C", "D"): params["cost_CD"],
        ("C", "E"): params["cost_CE"],
        ("D", "A"): params["cost_DA"],
        ("D", "B"): params["cost_DB"],
        ("D", "C"): params["cost_DC"],
        ("D", "E"): params["cost_DE"],
        ("E", "A"): params["cost_EA"],
        ("E", "B"): params["cost_EB"],
        ("E", "C"): params["cost_EC"],
        ("E", "D"): params["cost_ED"],
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

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
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
                ) <= len(subset) - 1
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}