import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    # Read travel costs from params (only for i != j)
    travel = {}
    for i in cities:
        for j in cities:
            if i != j:
                travel[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    # Decision variables: arc (i, j) used in the tour
    model.arc = pyo.Var(
        [(i, j) for i in cities for j in cities if i != j],
        domain=pyo.Binary,
    )

    # Objective: minimize total travel cost
    model.total_cost = pyo.Objective(
        expr=sum(travel[(i, j)] * model.arc[(i, j)]
                 for (i, j) in model.arc),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing arc
    model.out_cons = pyo.Constraint(
        cities,
        rule=lambda mdl, i: sum(mdl.arc[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_cons = pyo.Constraint(
        cities,
        rule=lambda mdl, j: sum(mdl.arc[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (DFJ) for all proper subsets of size 2 and 3.
    # For 4 cities, only size-2 subsets can form disjoint subtours,
    # but we include size-3 as well for completeness.
    from itertools import combinations

    sub_2 = list(combinations(cities, 2))
    sub_3 = list(combinations(cities, 3))
    subsets = sub_2 + sub_3
    model.subset_idx = pyo.Set(initialize=range(len(subsets)))

    def subtour_rule(mdl, k):
        S = subsets[k]
        return sum(mdl.arc[(i, j)]
                   for i in S for j in S if i != j) <= len(S) - 1

    model.subtour_cons = pyo.Constraint(model.subset_idx, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}