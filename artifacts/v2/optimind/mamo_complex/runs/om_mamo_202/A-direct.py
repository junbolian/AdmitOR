import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [1, 2, 3, 4, 5, 6]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params[f"c{i}{j}"]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.nodes, domain=pyo.Reals, bounds=(0, len(nodes) - 1))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in nodes if i != j) == 1
    model.out_cons = pyo.Constraint(model.nodes, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in nodes if i != j) == 1
    model.in_cons = pyo.Constraint(model.nodes, rule=in_rule)

    def subtour_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + (len(nodes) - 1) * m.x[(i, j)] <= len(nodes) - 2
        return pyo.Constraint.Skip
    model.subtour = pyo.Constraint(model.arcs, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}