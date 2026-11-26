# IR: {"sets":{"cities":["E","F","G","H","I"],"arcs":"ordered pairs of distinct cities","subsets":"all city subsets S with 2 <= |S| < num_cities"},"params":{"cost_u_v":"params['cost_u_v'] for every (u,v) in arcs","num_cities":"params['num_cities']; must equal len(cities)"},"variables":{"x[u,v]":"Binary for every (u,v) in arcs"},"constraints":["For each city u: sum(x[u,v] for v != u) = 1","For each city v: sum(x[u,v] for u != v) = 1","For each subset S: sum(x[u,v] for distinct u,v in S) <= |S|-1"],"objective":"Minimize sum(cost_u_v*x[u,v] for (u,v) in arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    num_cities = params["num_cities"]

    if num_cities != len(cities):
        return {"objective": None, "status": "invalid_num_cities"}

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

    arcs = tuple(costs)
    proper_subsets = tuple(
        subset
        for subset_size in range(2, len(cities))
        for subset in combinations(cities, subset_size)
    )

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
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

    model.outgoing_once = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming_once = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subset_ids = pyo.Set(
        initialize=range(len(proper_subsets)), ordered=True
    )

    def subtour_rule(instance, subset_id):
        subset = proper_subsets[subset_id]
        return sum(
            instance.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.subtour_elimination = pyo.Constraint(
        model.subset_ids, rule=subtour_rule
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}