# IR: {"sets":{"V":["E","F","G","H","I"],"A":"unordered pairs of distinct cities in V","S":"subsets of V with 2 <= size <= 4"},"params":{"cost_E_F":"real","cost_E_G":"real","cost_E_H":"real","cost_E_I":"real","cost_F_G":"real","cost_F_H":"real","cost_F_I":"real","cost_G_H":"real","cost_G_I":"real","cost_H_I":"real"},"variables":{"x[e in A]":"binary"},"constraints":["For each v in V: sum(x[e] for e incident to v) = 2","For each U in S: sum(x[e] for e contained in U) <= size(U)-1"],"objective":"minimize sum(cost_u_v * x[u,v] for (u,v) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    edges = tuple(combinations(cities, 2))
    costs = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("E", "I"): params["cost_E_I"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("F", "I"): params["cost_F_I"],
        ("G", "H"): params["cost_G_H"],
        ("G", "I"): params["cost_G_I"],
        ("H", "I"): params["cost_H_I"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.travel_cost = pyo.Param(
        model.edges, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[left, right]
            for left, right in edges
            if city == left or city == right
        ) == 2

    model.degree_limits = pyo.Constraint(model.cities, rule=degree_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
                sum(
                    model.x[left, right]
                    for left, right in combinations(subset, 2)
                )
                <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[left, right] * model.x[left, right]
            for left, right in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}