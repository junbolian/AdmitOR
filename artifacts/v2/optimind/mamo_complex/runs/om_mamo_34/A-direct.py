import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5, 6]

    arcs = [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 1), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
            (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
            (6, 1), (6, 2), (6, 3), (6, 4), (6, 5)]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Each city has exactly one outgoing arc
    model.out_balance = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_balance = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (DFJ lazy-style constraints enumerated over all proper
    # non-trivial subsets): internal arcs in any subset S of size 2..n-1 <= |S|-1
    from itertools import combinations
    subsets = []
    for k in range(2, len(cities)):
        for sub in combinations(cities, k):
            subsets.append(sub)
    model.subsets = pyo.Set(initialize=list(range(len(subsets))), ordered=True)
    model.subset_order = pyo.Constraint(
        model.subsets,
        rule=lambda m, s: sum(
            m.x[(i, j)]
            for i in subsets[s]
            for j in subsets[s]
            if i != j
        ) <= len(subsets[s]) - 1,
    )

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}