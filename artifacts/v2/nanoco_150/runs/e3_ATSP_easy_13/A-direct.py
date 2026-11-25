import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_nodes"])
    cost = params["cost_matrix"]

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1

    model.out_cons = pyo.Constraint(nodes, rule=out_rule)
    model.in_cons = pyo.Constraint(nodes, rule=in_rule)

    # MTZ subtour elimination (skip base node 0 as sequence anchor)
    def mtz_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2

    model.mtz_cons = pyo.Constraint(arcs, rule=mtz_rule)

    # fix u_0 = 0
    model.u0_cons = pyo.Constraint(expr=model.u[0] == 0)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}