import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def distance(i, j):
        a, b = min(i, j), max(i, j)
        return params["dist_%d_%d" % (a, b)]

    required = [(0, 1), (0, 3), (0, 6), (1, 5), (1, 6), (2, 3), (2, 4), (5, 7)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(required, domain=pyo.NonNegativeIntegers)
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals, bounds=(0, 7))

    def obj_rule(m):
        return sum(distance(i, j) * m.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.req_flow = pyo.ConstraintList()
    for (i, j) in required:
        model.req_flow.add(model.x[i, j] - model.y[i, j] >= 1)

    model.balance = pyo.ConstraintList()
    for k in nodes:
        model.balance.add(
            sum(model.x[k, j] for j in nodes if j != k)
            - sum(model.x[i, k] for i in nodes if i != k) == 0
        )

    model.mtz = pyo.ConstraintList()
    for (i, j) in arcs:
        if i != 0 and j != 0:
            model.mtz.add(model.u[i] - model.u[j] + 7 * model.x[i, j] <= 6)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}