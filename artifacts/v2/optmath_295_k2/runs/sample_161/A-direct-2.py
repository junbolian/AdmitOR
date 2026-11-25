import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 7
    cities = list(range(n))
    nodes = [i for i in range(1, n)]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals, bounds=(1, n - 1))

    model.obj = pyo.Objective(
        expr=sum(
            params["cost_%d_%d" % (i, j)] * model.x[(i, j)] for (i, j) in arcs
        ),
        sense=pyo.minimize,
    )

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.out_con = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    def mt_con(m, i, j):
        if i != j and i >= 1 and j >= 1:
            return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip
    model.mt_con = pyo.Constraint(cities, cities, rule=mt_con)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}