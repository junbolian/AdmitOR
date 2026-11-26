import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["A", "B", "C", "D", "E"]

    cost_keys = [k for k in params if k.startswith("cost_")]
    cost = {}
    for k in cost_keys:
        parts = k.split("_")
        i, j = parts[1], parts[3]
        cost[(i, j)] = params[k]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j],
        dimen=2,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, len(cities) - 1))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in m.cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in m.cities if i != j) == 1

    model.out_cons = pyo.Constraint(model.cities, rule=out_rule)
    model.in_cons = pyo.Constraint(model.cities, rule=in_rule)

    # Subtour elimination (MTZ) for non-root cities
    non_root = [c for c in cities if c != "A"]

    def mtz_rule(m, i, j):
        if i == j or i == "A" or j == "A":
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (len(cities) - 1) * m.x[(i, j)] <= (len(cities) - 2)

    model.mtz = pyo.Constraint(non_root, non_root, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}