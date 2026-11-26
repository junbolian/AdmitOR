import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ["E", "F", "G", "H", "I"]
    arcs = [(a, b) for a in cities for b in cities if a != b]

    cost = {(a, b): float(params["cost_" + a + b]) for (a, b) in arcs}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[a, b] * model.x[a, b] for (a, b) in arcs),
        sense=pyo.minimize,
    )

    # Each city is entered exactly once
    model.in_deg = pyo.Constraint(
        cities,
        rule=lambda m, c: sum(m.x[a, b] for (a, b) in arcs if b == c) == 1,
    )
    # Each city is left exactly once
    model.out_deg = pyo.Constraint(
        cities,
        rule=lambda m, c: sum(m.x[a, b] for (a, b) in arcs if a == c) == 1,
    )

    # Optional: subtour elimination (lightweight MTZ-free cut for 5 nodes)
    subsets = []
    for r in range(2, len(cities)):
        from itertools import combinations
        for combo in combinations(cities, r):
            subsets.append(set(combo))

    def subtour_rule(m, s):
        internal = [(a, b) for (a, b) in arcs if a in s and b in s]
        return sum(m.x[a, b] for (a, b) in internal) <= len(s) - 1

    model.subset_keys = pyo.Set(initialize=range(len(subsets)))
    model.sec = pyo.Constraint(
        model.subset_keys,
        rule=lambda m, k: subtour_rule(m, subsets[k]),
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}