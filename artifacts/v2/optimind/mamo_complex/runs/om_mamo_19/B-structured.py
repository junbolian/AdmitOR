# IR: {"sets":{"C":[1,2,3,4],"A":"{(i,j) in C x C: i != j}","S":"{T subset C: 2 <= |T| <= 3}"},"params":{"cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_2_1":"real","cost_2_3":"real","cost_2_4":"real","cost_3_1":"real","cost_3_2":"real","cost_3_4":"real","cost_4_1":"real","cost_4_2":"real","cost_4_3":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in C: sum(x[i,j] for j in C if j != i) = 1","For each j in C: sum(x[i,j] for i in C if i != j) = 1","For each T in S: sum(x[i,j] for i,j in T if i != j) <= |T|-1"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)
    subsets = tuple(
        subset
        for size in range(2, len(cities))
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
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, i):
        return sum(model.x[i, j] for j in model.cities if j != i) == 1

    def incoming_rule(model, j):
        return sum(model.x[i, j] for i in model.cities if i != j) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset in subsets:
        model.subtour_constraints.add(
            sum(model.x[i, j] for i in subset for j in subset if i != j)
            <= len(subset) - 1
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
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}