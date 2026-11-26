import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = int(params["N"])
    upper = params["distance_matrix"]

    # Build symmetric distance matrix from upper-triangular row-major entries (i<j).
    dist = [[0.0] * N for _ in range(N)]
    k = 0
    for i in range(N):
        for j in range(i + 1, N):
            dist[i][j] = upper[k]
            dist[j][i] = upper[k]
            k += 1

    nodes = range(N)
    # Directed arcs between distinct nodes.
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Subtour elimination using flow-based single-commodity formulation.
    # u[i] = position/order of node i in the tour (unused for depot).
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1

    model.out_cons = pyo.Constraint(nodes, rule=out_rule)
    model.in_cons = pyo.Constraint(nodes, rule=in_rule)

    # MTZ-style subtour elimination, depot fixed at node 0.
    M = N
    model.u[0].fix(0)

    def mtz_rule(m, i, j):
        if i == 0 or j == 0 or i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + M * m.x[i, j] <= M - 1

    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}