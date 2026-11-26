import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)
    cities = list(range(n))

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.A)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(model.C, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(model.C, rule=in_rule)

    # Subtour elimination via MTZ
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals, bounds=(1, n - 1))

    def mtz_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.A, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}