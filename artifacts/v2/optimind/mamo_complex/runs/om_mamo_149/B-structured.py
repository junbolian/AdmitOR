# IR: {"sets":{"cities":[1,2,3,4],"arcs":"(i,j) for distinct cities i,j","subsets":"all city subsets S with 2 <= |S| <= 3"},"params":{"cost_1_2":"arc cost","cost_1_3":"arc cost","cost_1_4":"arc cost","cost_2_1":"arc cost","cost_2_3":"arc cost","cost_2_4":"arc cost","cost_3_1":"arc cost","cost_3_2":"arc cost","cost_3_4":"arc cost","cost_4_1":"arc cost","cost_4_2":"arc cost","cost_4_3":"arc cost"},"variables":{"x[i,j]":{"type":"binary","index":"arcs"}},"constraints":["For each city i: sum(x[i,j] for j != i) = 1","For each city j: sum(x[i,j] for i != j) = 1","For each subset S: sum(x[i,j] for distinct i,j in S) <= |S|-1"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in arcs)"}}

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
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in problem.cities
            if destination != origin
        ) == 1

    def incoming_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in problem.cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_elimination.add(
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}