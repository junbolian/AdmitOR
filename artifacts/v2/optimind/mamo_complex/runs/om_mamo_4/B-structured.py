# IR: {"sets":{"V":[1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 4}"},"params":{"cost":"cost[i,j] = params['cost_i_j'] for every (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for every i in V","sum(x[i,j] for i in V if i != j) = 1 for every j in V","sum(x[i,j] for i in T for j in T if i != j) <= |T|-1 for every T in S"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (1, 2, 3, 4, 5)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    subsets = [
        subset
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    ]

    costs = {
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

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(
        model.A, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def outgoing_rule(problem, i):
        return sum(
            problem.x[i, j] for j in problem.V if j != i
        ) == 1

    def incoming_rule(problem, j):
        return sum(
            problem.x[i, j] for i in problem.V if i != j
        ) == 1

    model.outgoing = pyo.Constraint(model.V, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.V, rule=incoming_rule)

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
            model.cost[i, j] * model.x[i, j]
            for i, j in model.A
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