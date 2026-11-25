import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = len(dist)

    model = pyo.ConcreteModel()

    model.NODES = pyo.RangeSet(0, n - 1)
    model.ARCS = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
    )

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in m.ARCS)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in range(n) if j != i) == 1

    model.out_flow = pyo.Constraint(model.NODES, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in range(n) if i != j) == 1

    model.in_flow = pyo.Constraint(model.NODES, rule=in_rule)

    # MTZ subtour elimination with continuous order variables
    model.u = pyo.Var(model.NODES, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def mtz_rule(m, i, j):
        if i != 0 and j != 0 and i != j:
            return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.ARCS, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}