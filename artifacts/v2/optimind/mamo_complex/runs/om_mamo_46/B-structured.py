# IR: {"sets":{"cities":[1,2,3,4],"arcs":"(i,j) in cities x cities where i != j","subsets":"all city subsets S with 2 <= |S| <= 3"},"params":["cost_1_2","cost_1_3","cost_1_4","cost_2_1","cost_2_3","cost_2_4","cost_3_1","cost_3_2","cost_3_4","cost_4_1","cost_4_2","cost_4_3"],"variables":{"x[i,j]":"binary for each arc (i,j)"},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for i,j in S where i != j) <= |S|-1"],"objective":"minimize sum(cost_i_j * x[i,j] for all arcs (i,j))"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    subsets = tuple(
        subset
        for subset_size in (2, 3)
        for subset in combinations(cities, subset_size)
    )
    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(mod, origin):
        return sum(
            mod.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(mod, destination):
        return sum(
            mod.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_limits.add(
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
        # HiGHS can raise when no feasible solution is available to load.
        # Determine success below solely by objective retrieval.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}