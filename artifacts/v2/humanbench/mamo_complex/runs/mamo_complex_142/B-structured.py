# IR: {"sets":{"V":[1,2,3,4],"A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| <= 3}"},"params":{"travel_cost_c1_c2":"cost[1,2]","travel_cost_c1_c3":"cost[1,3]","travel_cost_c1_c4":"cost[1,4]","travel_cost_c2_c1":"cost[2,1]","travel_cost_c2_c3":"cost[2,3]","travel_cost_c2_c4":"cost[2,4]","travel_cost_c3_c1":"cost[3,1]","travel_cost_c3_c2":"cost[3,2]","travel_cost_c3_c4":"cost[3,4]","travel_cost_c4_c1":"cost[4,1]","travel_cost_c4_c2":"cost[4,2]","travel_cost_c4_c3":"cost[4,3]"},"variables":{"x[i,j]":{"domain":"Binary","indices":"A"}},"constraints":["outgoing[i in V]: sum(x[i,j] for j in V if j != i) = 1","incoming[j in V]: sum(x[i,j] for i in V if i != j) = 1","subtour[U in S]: sum(x[i,j] for i in U for j in U if i != j) <= |U|-1"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in A)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    subsets = [
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    ]

    costs = {
        (1, 2): params["travel_cost_c1_c2"],
        (1, 3): params["travel_cost_c1_c3"],
        (1, 4): params["travel_cost_c1_c4"],
        (2, 1): params["travel_cost_c2_c1"],
        (2, 3): params["travel_cost_c2_c3"],
        (2, 4): params["travel_cost_c2_c4"],
        (3, 1): params["travel_cost_c3_c1"],
        (3, 2): params["travel_cost_c3_c2"],
        (3, 4): params["travel_cost_c3_c4"],
        (4, 1): params["travel_cost_c4_c1"],
        (4, 2): params["travel_cost_c4_c2"],
        (4, 3): params["travel_cost_c4_c3"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(model.arcs, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour = pyo.ConstraintList()
    for subset in subsets:
        model.subtour.add(
            sum(
                model.x[i, j]
                for i in subset
                for j in subset
                if i != j
            ) <= len(subset) - 1
        )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i, j] * model.x[i, j] for i, j in model.arcs),
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