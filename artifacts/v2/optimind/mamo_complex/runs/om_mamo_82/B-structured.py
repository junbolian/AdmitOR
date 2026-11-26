# IR: {"sets":{"C":[1,2,3,4],"A":"{(i,j) in C x C: i != j}","S":"{T subset C: 2 <= |T| <= 3}"},"params":{"cost_12":"params['cost_12']","cost_13":"params['cost_13']","cost_14":"params['cost_14']","cost_21":"params['cost_21']","cost_23":"params['cost_23']","cost_24":"params['cost_24']","cost_31":"params['cost_31']","cost_32":"params['cost_32']","cost_34":"params['cost_34']","cost_41":"params['cost_41']","cost_42":"params['cost_42']","cost_43":"params['cost_43']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","sum(x[i,j] for i in T for j in T if i != j) <= |T|-1 for T in S"],"objective":"minimize sum(cost_ij*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)
    costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(model, i):
        return sum(
            model.x[i, j] for j in model.cities if j != i
        ) == 1

    def incoming_rule(model, j):
        return sum(
            model.x[i, j] for i in model.cities if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_constraints.add(
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
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}