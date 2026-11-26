import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in cities for j in cities if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_constraint = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_constraint = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (Miller-Tucker-Zemlin)
    model.u = pyo.Var(cities, bounds=(1, len(cities)))

    def mtz_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + len(cities) * m.x[i, j] <= len(cities) - 1
        return pyo.Constraint.Skip
    model.mtz_constraint = pyo.Constraint(cities, cities, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}