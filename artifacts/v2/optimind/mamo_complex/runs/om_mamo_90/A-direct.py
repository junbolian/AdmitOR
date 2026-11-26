import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5, 6]

    model = pyo.ConcreteModel()

    # Cost lookup from params
    def cost_of(i, j):
        return params["c_%d%d" % (i, j)]

    # Decision variables: x[i,j] == 1 if travel directly from i to j
    model.x = pyo.Var(cities, cities, domain=pyo.Binary)
    for i in cities:
        for j in cities:
            if i == j:
                model.x[i, j].fix(0)

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(cost_of(i, j) * m.x[i, j] for i in cities for j in cities if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ formulation with continuous order variable u)
    # u[i] for i in 2..6, bounded in [2, 6]; skip depot city 1.
    others = [2, 3, 4, 5, 6]
    model.u = pyo.Var(others, bounds=(2, len(cities)))

    def mtz_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + len(cities) * m.x[i, j] <= len(cities) - 1
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(cities, cities, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}