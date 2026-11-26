# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","S":"{U subset V: 2 <= |U| <= 5}"},"params":{"c_12":"arc cost","c_13":"arc cost","c_14":"arc cost","c_15":"arc cost","c_16":"arc cost","c_21":"arc cost","c_23":"arc cost","c_24":"arc cost","c_25":"arc cost","c_26":"arc cost","c_31":"arc cost","c_32":"arc cost","c_34":"arc cost","c_35":"arc cost","c_36":"arc cost","c_41":"arc cost","c_42":"arc cost","c_43":"arc cost","c_45":"arc cost","c_46":"arc cost","c_51":"arc cost","c_52":"arc cost","c_53":"arc cost","c_54":"arc cost","c_56":"arc cost","c_61":"arc cost","c_62":"arc cost","c_63":"arc cost","c_64":"arc cost","c_65":"arc cost"},"variables":{"x[i,j]":{"index":"A","type":"binary"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each U in S: sum(x[i,j] for i in U for j in U if i != j) <= |U| - 1"],"objective":{"sense":"minimize","expression":"sum(c_ij * x[i,j] for (i,j) in A)"}}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (1, 2): params["c_12"],
        (1, 3): params["c_13"],
        (1, 4): params["c_14"],
        (1, 5): params["c_15"],
        (1, 6): params["c_16"],
        (2, 1): params["c_21"],
        (2, 3): params["c_23"],
        (2, 4): params["c_24"],
        (2, 5): params["c_25"],
        (2, 6): params["c_26"],
        (3, 1): params["c_31"],
        (3, 2): params["c_32"],
        (3, 4): params["c_34"],
        (3, 5): params["c_35"],
        (3, 6): params["c_36"],
        (4, 1): params["c_41"],
        (4, 2): params["c_42"],
        (4, 3): params["c_43"],
        (4, 5): params["c_45"],
        (4, 6): params["c_46"],
        (5, 1): params["c_51"],
        (5, 2): params["c_52"],
        (5, 3): params["c_53"],
        (5, 4): params["c_54"],
        (5, 6): params["c_56"],
        (6, 1): params["c_61"],
        (6, 2): params["c_62"],
        (6, 3): params["c_63"],
        (6, 4): params["c_64"],
        (6, 5): params["c_65"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 7)
            for j in range(1, 7)
            if i != j
        ],
    )
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
    for subset_size in range(2, 6):
        for subset in combinations(range(1, 7), subset_size):
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
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}