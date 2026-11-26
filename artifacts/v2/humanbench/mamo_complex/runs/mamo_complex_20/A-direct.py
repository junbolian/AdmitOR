import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_cities"])
    cities = list(range(1, n + 1))

    cost = {}
    for a in cities:
        for b in cities:
            if a != b:
                cost[(a, b)] = float(params["cost_%d_%d" % (a, b)])

    model = pyo.ConcreteModel()
    model.CITY = pyo.Set(initialize=cities)
    model.ARC = pyo.Set(initialize=[(a, b) for a in cities for b in cities if a != b])
    model.x = pyo.Var(model.ARC, domain=pyo.Binary)
    model.u = pyo.Var(model.CITY, domain=pyo.NonNegativeReals, bounds=(1, n))

    @model.Objective(sense=pyo.minimize)
    def total_cost(m):
        return sum(cost[(a, b)] * m.x[(a, b)] for (a, b) in m.ARC)

    @model.Constraint(model.CITY)
    def out_flow(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    @model.Constraint(model.CITY)
    def in_flow(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    @model.Constraint(model.ARC)
    def subtour(m, i, j):
        if j == 1:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}