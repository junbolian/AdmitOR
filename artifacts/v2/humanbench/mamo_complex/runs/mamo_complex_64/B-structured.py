# IR: {"sets":{"V":["E","F","G","H","I"],"A":"unordered pairs of distinct cities in V","S":"subsets of V with 2 <= cardinality <= 4"},"params":{"cost_E_to_F":"cost of {E,F}","cost_E_to_G":"cost of {E,G}","cost_E_to_H":"cost of {E,H}","cost_E_to_I":"cost of {E,I}","cost_F_to_G":"cost of {F,G}","cost_F_to_H":"cost of {F,H}","cost_F_to_I":"cost of {F,I}","cost_G_to_H":"cost of {G,H}","cost_G_to_I":"cost of {G,I}","cost_H_to_I":"cost of {H,I}"},"variables":{"x[a]":"Binary for each a in A; 1 if the route uses edge a"},"constraints":["For each v in V: sum(x[a] for a incident to v) = 2","For each T in S: sum(x[a] for a contained in T) <= cardinality(T)-1"],"objective":"Minimize sum(cost[a]*x[a] for a in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    edges = tuple(combinations(cities, 2))
    subsets = tuple(
        frozenset(subset)
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    edge_costs = {
        ("E", "F"): params["cost_E_to_F"],
        ("E", "G"): params["cost_E_to_G"],
        ("E", "H"): params["cost_E_to_H"],
        ("E", "I"): params["cost_E_to_I"],
        ("F", "G"): params["cost_F_to_G"],
        ("F", "H"): params["cost_F_to_H"],
        ("F", "I"): params["cost_F_to_I"],
        ("G", "H"): params["cost_G_to_H"],
        ("G", "I"): params["cost_G_to_I"],
        ("H", "I"): params["cost_H_to_I"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.subtour_keys = pyo.Set(
        initialize=range(len(subsets)), ordered=True
    )

    model.edge_cost = pyo.Param(
        model.edges, initialize=edge_costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[left, right]
            for left, right in edges
            if left == city or right == city
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    def subtour_rule(instance, subset_key):
        subset = subsets[subset_key]
        return sum(
            instance.x[left, right]
            for left, right in edges
            if left in subset and right in subset
        ) <= len(subset) - 1

    model.subtour_constraints = pyo.Constraint(
        model.subtour_keys, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[left, right] * model.x[left, right]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}