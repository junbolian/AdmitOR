import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_cities"])
    D = params["distance_matrix"]

    cities = list(range(n))

    def dist(i, j):
        return D[i][j]

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(dimen=2, initialize=[(i, j) for i in cities for j in cities if i != j])

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(m):
        return sum(dist(i, j) * m.x[i, j] for (i, j) in m.A)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.C if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.C if i != j) == 1

    model.out_cons = pyo.Constraint(model.C, rule=out_rule)
    model.in_cons = pyo.Constraint(model.C, rule=in_rule)

    def mtz_rule(m, i, j):
        if i != j and i != cities[0] and j != cities[0]:
            return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(model.A, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}