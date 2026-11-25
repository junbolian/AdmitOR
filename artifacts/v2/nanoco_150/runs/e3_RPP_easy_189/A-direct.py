import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    dist = params["distance_matrix"]
    depot = params["depot_node"]
    n = len(dist)

    required_edges = [(1, 8), (2, 3), (3, 4), (3, 6), (3, 8), (4, 8), (5, 7), (7, 8)]

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.req_edges = pyo.Set(initialize=required_edges, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def flow_rule(m, k):
        return (
            sum(m.x[k, j] for j in range(n) if j != k)
            == sum(m.x[i, k] for i in range(n) if i != k)
        )
    model.flow = pyo.Constraint(range(n), rule=flow_rule)

    model.depot_out = pyo.Constraint(
        expr=sum(model.x[depot, j] for j in range(n) if j != depot) >= 1
    )

    order = sorted([k for k in range(n) if k != depot], key=lambda k: dist[depot][k])
    N = len(order)

    model.u = pyo.Var(order, domain=pyo.NonNegativeReals, bounds=(0, N))

    def mtz_rule(m, i, j):
        if i != depot and j != depot and i != j:
            return m.u[i] - m.u[j] + N * m.x[i, j] <= N - 1
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    def req_rule(m, a, b):
        return m.x[a, b] + m.x[b, a] >= 1
    model.required = pyo.Constraint(model.req_edges, rule=req_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}