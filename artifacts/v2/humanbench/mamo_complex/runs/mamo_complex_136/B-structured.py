# IR: {"sets":{"V":[1,2,3,4,5],"A":"{(i,j) in V x V : i != j}","S":"{U subset V : 2 <= |U| <= 4}"},"params":["cost_1_2","cost_1_3","cost_1_4","cost_1_5","cost_2_1","cost_2_3","cost_2_4","cost_2_5","cost_3_1","cost_3_2","cost_3_4","cost_3_5","cost_4_1","cost_4_2","cost_4_3","cost_4_5","cost_5_1","cost_5_2","cost_5_3","cost_5_4"],"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for each i in V","sum(x[i,j] for i in V if i != j) = 1 for each j in V","sum(x[i,j] for i in U for j in U if i != j) <= |U|-1 for each U in S"],"objective":"minimize sum(cost_i_j * x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    travel_costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
        (4, 5): params["cost_4_5"],
        (5, 1): params["cost_5_1"],
        (5, 2): params["cost_5_2"],
        (5, 3): params["cost_5_3"],
        (5, 4): params["cost_5_4"],
    }

    cities = tuple(range(1, 6))
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=travel_costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(current_model, i):
        return sum(
            current_model.x[i, j]
            for j in current_model.cities
            if j != i
        ) == 1

    def incoming_rule(current_model, j):
        return sum(
            current_model.x[i, j]
            for i in current_model.cities
            if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_elimination = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_elimination.add(
                sum(
                    model.x[i, j]
                    for i in subset
                    for j in subset
                    if i != j
                ) <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
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