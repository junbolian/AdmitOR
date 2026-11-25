import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.u = pyo.Var(model.nodes, domain=pyo.NonNegativeReals, bounds=(0, 3))
    model.u[0].fix(0)

    def obj_rule(m):
        return sum(
            params["cost_{}_{}".format(i, j)] * m.x[i, j]
            for (i, j) in m.arcs
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_once = pyo.Constraint(model.nodes, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_once = pyo.Constraint(model.nodes, rule=in_rule)

    non_zero = [1, 2, 3]

    def subtour_rule(m, i, j):
        if i != j:
            return m.u[j] >= m.u[i] + 1 - 4 * (1 - m.x[i, j])
        return pyo.Constraint.Skip
    model.subtour = pyo.Constraint(non_zero, non_zero, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}