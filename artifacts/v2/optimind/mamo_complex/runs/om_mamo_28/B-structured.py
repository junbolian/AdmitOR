# IR: {"sets":{"V":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","S":"{S subset V: 2 <= |S| <= 3}"},"params":{"cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_2_1":"real","cost_2_3":"real","cost_2_4":"real","cost_3_1":"real","cost_3_2":"real","cost_3_4":"real","cost_4_1":"real","cost_4_2":"real","cost_4_3":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for each i in V","sum(x[i,j] for i in V if i != j) = 1 for each j in V","sum(x[i,j] for i in S for j in S if i != j) <= |S|-1 for each S in S"],"objective":"minimize sum(cost_i_j * x[i,j] for (i,j) in A)"}

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
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.subset_ids = pyo.Set(initialize=range(len(subsets)), ordered=True)

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

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    def subtour_rule(instance, subset_id):
        subset = subsets[subset_id]
        return sum(
            instance.x[origin, destination]
            for origin in subset
            for destination in subset
            if origin != destination
        ) <= len(subset) - 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}