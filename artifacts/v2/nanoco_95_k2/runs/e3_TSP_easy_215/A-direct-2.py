import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = len(dist)
    nodes = list(range(n))

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
    )

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    # Ordering variables for subtour elimination (MTZ), defined for outlets 1..n-1
    model.u = pyo.Var(model.NODES, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in model.ARCS),
        sense=pyo.minimize,
    )

    # Each node has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in nodes if j != i) == 1
    model.out_con = pyo.Constraint(model.NODES, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1
    model.in_con = pyo.Constraint(model.NODES, rule=in_rule)

    # MTZ subtour elimination
    model.MTZ = pyo.ConstraintList()
    for i in nodes:
        if i != 0:
            model.MTZ.add(model.u[i] >= 1)
            model.MTZ.add(model.u[i] <= n - 1)
    for (i, j) in model.ARCS:
        if i != 0 and j != 0:
            model.MTZ.add(model.u[i] - model.u[j] + (n - 1) * model.x[i, j] <= n - 2)

    model.u[0].fix(0)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}