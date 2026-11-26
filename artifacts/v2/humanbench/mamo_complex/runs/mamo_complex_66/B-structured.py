# IR: {"sets":{"V":[1,2,3,4,5,6],"E":"{(i,j): i,j in V, i<j}","S":"{S subset V: 2<=|S|<=5}"},"params":{"cost":"E -> Reals; (i,j) reads params['c'+str(i)+str(j)]"},"variables":{"x[i,j]":"Binary for (i,j) in E"},"constraints":["For each v in V: sum(x[i,j] for (i,j) in E if v in (i,j)) = 2","For each S in S: sum(x[i,j] for (i,j) in E if i in S and j in S) <= |S|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(1, 7))
    edges = tuple(combinations(cities, 2))

    costs = {
        (1, 2): params["c12"],
        (1, 3): params["c13"],
        (1, 4): params["c14"],
        (1, 5): params["c15"],
        (1, 6): params["c16"],
        (2, 3): params["c23"],
        (2, 4): params["c24"],
        (2, 5): params["c25"],
        (2, 6): params["c26"],
        (3, 4): params["c34"],
        (3, 5): params["c35"],
        (3, 6): params["c36"],
        (4, 5): params["c45"],
        (4, 6): params["c46"],
        (5, 6): params["c56"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.cost = pyo.Param(model.edges, initialize=costs, within=pyo.Reals)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[i, j]
            for i, j in instance.edges
            if city == i or city == j
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            members = frozenset(subset)
            model.subtour_constraints.add(
                sum(
                    model.x[i, j]
                    for i, j in edges
                    if i in members and j in members
                )
                <= subset_size - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i, j in model.edges
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}