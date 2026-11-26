import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    d = params["d"]
    c = params["c"]

    n = len(d)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n - 1)
    model.L = pyo.RangeSet(0, n - 1)

    # y[i, p] = 1 if factory i is assigned to location p
    model.x = pyo.Var(model.I, model.L, domain=pyo.Binary)

    # Linearized objective via auxiliary variable z[i,j,p,q] = x[i,p]*x[j,q]
    # Transportation cost: sum_{i,j} d_ij * c_{assigned loc of i, assigned loc of j}
    # Linearize the product of two binaries.
    model.P = pyo.Set(initialize=[(i, j) for i in model.I for j in model.I])
    model.Q = pyo.Set(initialize=[(p, q) for p in model.L for q in model.L])
    model.z = pyo.Var(model.P, model.Q, domain=pyo.Binary)

    # Linearization constraints for z[i,j,p,q] = x[i,p] * x[j,q]
    def lin1_rule(m, i, j, p, q):
        return m.z[i, j, p, q] <= m.x[i, p]

    def lin2_rule(m, i, j, p, q):
        return m.z[i, j, p, q] <= m.x[j, q]

    def lin3_rule(m, i, j, p, q):
        return m.z[i, j, p, q] >= m.x[i, p] + m.x[j, q] - 1

    model.lin1 = pyo.Constraint(model.P, model.Q, rule=lin1_rule)
    model.lin2 = pyo.Constraint(model.P, model.Q, rule=lin2_rule)
    model.lin3 = pyo.Constraint(model.P, model.Q, rule=lin3_rule)

    def obj_rule(m):
        return sum(
            d[i][j] * c[p][q] * m.z[i, j, p, q]
            for i in model.I for j in model.I
            for p in model.L for q in model.L
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def factory_rule(m, i):
        return sum(m.x[i, p] for p in m.L) == 1

    model.factory_con = pyo.Constraint(model.I, rule=factory_rule)

    def location_rule(m, p):
        return sum(m.x[i, p] for i in model.I) == 1

    model.location_con = pyo.Constraint(model.L, rule=location_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}