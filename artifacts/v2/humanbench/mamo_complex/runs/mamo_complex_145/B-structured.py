# IR: {"sets":{"cities":[1,2,3,4],"arcs":"{(i,j): i,j in cities, i != j}","subsets":"{S subset of cities: 2 <= |S| <= 3}"},"params":{"cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_2_1":"real","cost_2_3":"real","cost_2_4":"real","cost_3_1":"real","cost_3_2":"real","cost_3_4":"real","cost_4_1":"real","cost_4_2":"real","cost_4_3":"real"},"variables":{"x[i,j]":"binary for (i,j) in arcs"},"constraints":["For each i in cities: sum(x[i,j] for j != i) = 1","For each j in cities: sum(x[i,j] for i != j) = 1","For each S in subsets: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":"minimize sum(cost_i_j * x[i,j] for (i,j) in arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)
    subsets = tuple(
        subset
        for size in (2, 3)
        for subset in combinations(cities, size)
    )

    costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(mod, i):
        return sum(mod.x[i, j] for j in cities if j != i) == 1

    def incoming_rule(mod, j):
        return sum(mod.x[i, j] for i in cities if i != j) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_limits.add(
            sum(
                model.x[i, j]
                for i in subset
                for j in subset
                if i != j
            )
            <= len(subset) - 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j] for i, j in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}