import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def cost(i, j):
        return params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var([1, 2, 3, 4], bounds=(1, 4))

    def obj_rule(m):
        return sum(cost(i, j) * m.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.depart = pyo.Constraint(cities, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.arrive = pyo.Constraint(cities, rule=arrive_rule)

    def order_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + 1 - (len(cities) - 1) * (1 - m.x[i, j])

    model.order = pyo.Constraint(arcs, rule=order_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}