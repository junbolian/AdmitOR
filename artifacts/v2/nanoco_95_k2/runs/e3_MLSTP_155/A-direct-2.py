import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sensor_coordinates = params["sensor_coordinates"]
    edge_distances = params["edge_distances"]
    n_sensors = params["n_sensors"]
    n_candidate_edges = params["n_candidate_edges"]

    # Candidate edges are implied by edge_distances structure (non-zero entries
    # among the listed pairs). Reconstruct the candidate set from the params.
    n = int(n_sensors)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            d = edge_distances[i][j]
            if d is not None and d != 0:
                edges.append((i, j))
    E = len(edges)

    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, n - 1)
    model.E = pyo.RangeSet(0, E - 1)

    def edge_tail(m, e):
        return edges[e][0]

    def edge_head(m, e):
        return edges[e][1]

    # Incidence: for each node, list of edge indices
    inc = {v: [] for v in range(n)}
    for e, (i, j) in enumerate(edges):
        inc[i].append(e)
        inc[j].append(e)

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    # Degree of each node
    def degree_expr(m, v):
        return sum(m.x[e] for e in inc[v])

    model.degree = pyo.Expression(model.V, rule=degree_expr)

    # Flows for connectivity (single-commodity flow rooted at node 0)
    model.f = pyo.Var(model.E, domain=pyo.NonNegativeReals)
    # orient flow: introduce direction variables? Use undirected with signed bounds:
    # Simpler: each edge carries 0..n flow, root sends n-1 units.
    model.f = pyo.Var(model.E, bounds=(0, n))

    # Net flow constraint at each non-root node: inflow - outflow = 1
    # At root: outflow - inflow = n-1
    # We treat edges as directed arbitrarily based on (tail, head) ordering.
    def flow_balance(m, v):
        expr = 0
        for e, (i, j) in enumerate(edges):
            if i == v:
                expr -= m.f[e]
            elif j == v:
                expr += m.f[e]
        if v == 0:
            return expr == -(n - 1)
        else:
            return expr == 1

    model.flow_balance = pyo.Constraint(model.V, rule=flow_balance)

    # Capacity: flow on edge <= n * x
    def cap_rule(m, e):
        return m.f[e] <= n * m.x[e]

    model.cap = pyo.Constraint(model.E, rule=cap_rule)

    # Total edges = n - 1 (spanning tree)
    model.n_edges = pyo.Constraint(expr=sum(model.x[e] for e in model.E) == n - 1)

    # Degree indicator for peripheral (degree == 1)
    model.y = pyo.Var(model.V, domain=pyo.Binary)

    # degree[v] == 1  <=>  y[v] == 1
    # degree >= 1 always (connected), and degree >= 2(1 - y)
    def y_lb(m, v):
        return m.degree[v] >= 2 * (1 - m.y[v])

    def y_ub(m, v):
        return m.degree[v] <= 1 + n * (1 - m.y[v])

    model.y_lb = pyo.Constraint(model.V, rule=y_lb)
    model.y_ub = pyo.Constraint(model.V, rule=y_ub)

    model.obj = pyo.Objective(expr=sum(model.y[v] for v in model.V), sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}