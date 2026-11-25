import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]

    nodes = list(range(15))
    edges_list = [
        (4, 6), (12, 13), (3, 10), (5, 10), (2, 5), (1, 3), (0, 14), (0, 11),
        (10, 12), (11, 14), (1, 12), (6, 11), (6, 8), (6, 14), (4, 5), (3, 9),
        (4, 8), (3, 12), (9, 10), (2, 4), (2, 7), (1, 5), (2, 13), (4, 7),
        (4, 10), (0, 6), (1, 13), (1, 10), (6, 9), (7, 8),
    ]
    # canonical undirected edges
    edges = []
    seen = set()
    for i, j in edges_list:
        key = (min(i, j), max(i, j))
        if key not in seen:
            seen.add(key)
            edges.append(key)
    edge_index = list(range(len(edges)))

    # incidence lists
    incident = {v: [] for v in nodes}
    for e_idx in edge_index:
        i, j = edges[e_idx]
        incident[i].append(e_idx)
        incident[j].append(e_idx)

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes)
    model.E = pyo.Set(initialize=edge_index)

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    # y[v] = 1 if node v is peripheral (degree exactly 1)
    model.y = pyo.Var(model.V, domain=pyo.Binary)

    def deg_expr(v):
        return sum(model.x[e] for e in incident[v])

    # Spanning tree: exactly |V| - 1 edges
    model.spanning = pyo.Constraint(
        expr=sum(model.x[e] for e in model.E) == len(nodes) - 1
    )

    # y[v] = 1  <=>  degree(v) == 1
    # degree >= 1 - y  (if y=1 then degree >= 1)
    # degree <= 1 + (n-1)(1-y)  (if y=1 then degree <= 1)
    # also if y=0, degree can be 0 or >=2; but connectivity handles degree>=1.
    def low_rule(m, v):
        return deg_expr(v) >= 1 - model.y[v]

    def up_rule(m, v):
        return deg_expr(v) <= 1 + (len(nodes) - 2) * (1 - model.y[v])

    model.deg_low = pyo.Constraint(model.V, rule=low_rule)
    model.deg_up = pyo.Constraint(model.V, rule=up_rule)

    # Connectivity via single-commodity flow rooted at node 0
    # f[e, direction] binary-ish flow; use continuous flow on oriented arcs.
    # For each edge, two directed arcs.
    arcs = []
    for e_idx in edge_index:
        i, j = edges[e_idx]
        arcs.append((e_idx, i, j))
        arcs.append((e_idx, j, i))
    arc_index = list(range(len(arcs)))

    model.A = pyo.Set(initialize=arc_index)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    root = 0
    # flow conservation: for v != root, inflow - outflow = 1 (each non-root receives one unit)
    out_arcs = {v: [] for v in nodes}
    in_arcs = {v: [] for v in nodes}
    for a_idx in arc_index:
        e_idx, u, w = arcs[a_idx]
        out_arcs[u].append((a_idx, e_idx))
        in_arcs[w].append((a_idx, e_idx))

    def flow_rule(m, v):
        if v == root:
            return pyo.Constraint.Skip
        inflow = sum(model.f[a] for (a, _e) in in_arcs[v])
        outflow = sum(model.f[a] for (a, _e) in out_arcs[v])
        return inflow - outflow == 1

    model.flow_bal = pyo.Constraint(model.V, rule=flow_rule)

    def cap_rule(m, a_idx):
        _e_idx, _u, _w = arcs[a_idx]
        return model.f[a_idx] <= len(nodes) * model.x[_e_idx]

    model.flow_cap = pyo.Constraint(model.A, rule=cap_rule)

    model.obj = pyo.Objective(expr=sum(model.y[v] for v in model.V), sense=pyo.maximize)

    Highs().solve(model)
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "no feasible solution found"}

    return {"objective": obj_val, "status": "optimal"}