# IR: {"sets":{"cities":[1,2,3,4],"arcs":"(i,j) for distinct cities i,j","subsets":"all city subsets S with 2 <= |S| <= 3"},"params":{"cost":"arc costs read from params: cost_1_2,cost_1_3,cost_1_4,cost_2_1,cost_2_3,cost_2_4,cost_3_1,cost_3_2,cost_3_4,cost_4_1,cost_4_2,cost_4_3"},"variables":{"x[i,j]":"Binary for each arc (i,j)"},"constraints":{"outgoing":"sum(x[i,j] for j != i) == 1 for each city i","incoming":"sum(x[i,j] for i != j) == 1 for each city j","subtour":"sum(x[i,j] for distinct i,j in S) <= |S|-1 for each subset S"},"objective":"minimize sum(cost[i,j]*x[i,j] for each arc (i,j))"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)
    subsets = tuple(
        subset
        for subset_size in range(2, len(cities))
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
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
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
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}