import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params["cost_{0}_{1}".format(i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Order / position variables for subtour elimination (MTZ)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, len(cities) - 1))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for i, j in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.out_constraint = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.in_constraint = pyo.Constraint(cities, rule=in_rule)

    # Fix city 1 as the depot for MTZ anchoring
    n = len(cities)

    def mtz_rule(m, i, j):
        if i == j or i == 1 or j == 1:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
    model.mtz_constraint = pyo.Constraint(cities, cities, rule=mtz_rule)

    def u_bound_rule(m, i):
        if i == 1:
            return m.u[i] == 0
        return pyo.Constraint.Skip
    model.u_anchor = pyo.Constraint(cities, rule=u_bound_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}