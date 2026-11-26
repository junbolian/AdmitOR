import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
from itertools import combinations


def solve(params):
    cities = [1, 2, 3, 4]
    edges = [(i, j) for i in cities for j in cities if i != j]

    cost = {
        (1, 2): params["cost_12"], (1, 3): params["cost_13"], (1, 4): params["cost_14"],
        (2, 1): params["cost_21"], (2, 3): params["cost_23"], (2, 4): params["cost_24"],
        (3, 1): params["cost_31"], (3, 2): params["cost_32"], (3, 4): params["cost_34"],
        (4, 1): params["cost_41"], (4, 2): params["cost_42"], (4, 3): params["cost_43"],
    }

    model = pyo.ConcreteModel()
    model.x = pyo.Var(edges, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in edges),
        sense=pyo.minimize,
    )

    # Each city entered exactly once
    model.in_deg = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )
    # Each city left exactly once
    model.out_deg = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Subtour elimination (DFJ) for all proper non-empty subsets of size >= 2
    subsets = []
    for k in range(2, len(cities)):
        for sub in combinations(cities, k):
            subsets.append(set(sub))

    def subtour_rule(m, s_idx):
        S = subsets[s_idx]
        expr = sum(m.x[(i, j)] for (i, j) in edges if i in S and j in S)
        return expr <= len(S) - 1

    model.subtours = pyo.Constraint(
        range(len(subsets)),
        rule=subtour_rule,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}