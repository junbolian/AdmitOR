import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]

    N = 5
    cities = list(range(N))
    other = [i for i in cities if i != 0]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(cities, cities, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in cities for j in cities if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1

    model.depart = pyo.Constraint(cities, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1

    model.arrive = pyo.Constraint(cities, rule=arrive_rule)

    def mtov_rule(m, i, j):
        if j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + 1 - N * (1 - m.x[i, j])

    model.mtov = pyo.Constraint(cities, cities, rule=mtov_rule)

    def u_bound_rule(m, i):
        if i == 0:
            return pyo.Constraint.Skip
        return pyo.inequality(1, m.u[i], N - 1)

    model.u_bound = pyo.Constraint(cities, rule=u_bound_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}