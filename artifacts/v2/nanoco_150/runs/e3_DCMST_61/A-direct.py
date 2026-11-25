import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["device_coordinates"]
    dist = params["distance_matrix"]
    max_deg = params["max_degree"]

    n = len(coords)
    nodes = list(range(n))

    # Directed edge set: only i < j pairs, represented with an orientation
    edges = [(i, j) for i in nodes for j in nodes if i < j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    # x[i,j] = 1 if undirected edge {i,j} is selected (i<j)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    # Flow variables for single-commodity flow connectivity + cycle prevention.
    # Node 0 is the root. f[i,j] = flow along directed arc i->j.
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals,
                      bounds=(0, n - 1))

    def cost_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in edges)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Degree constraints: each node has at most max_deg selected edges
    def degree_rule(m, v):
        terms = []
        for (i, j) in edges:
            if i == v:
                terms.append(m.x[i, j])
            elif j == v:
                terms.append(m.x[i, j])
        return sum(terms) <= max_deg
    model.degree_con = pyo.Constraint(model.nodes, rule=degree_rule)

    # Connectivity via flow: root sends n-1 units; every other node consumes 1.
    # Flow can only traverse selected edges.
    def flow_capacity_rule(m, i, j):
        if i < j:
            return m.f[i, j] + m.f[j, i] <= (n - 1) * m.x[i, j]
        else:
            return pyo.Constraint.Skip
    model.flow_cap = pyo.Constraint(model.arcs, rule=flow_capacity_rule)

    def flow_balance_root(m, v):
        if v == 0:
            out_flow = sum(m.f[0, j] for j in nodes if j != 0)
            in_flow = sum(m.f[j, 0] for j in nodes if j != 0)
            return out_flow - in_flow == n - 1
        else:
            out_flow = sum(m.f[v, j] for j in nodes if j != v)
            in_flow = sum(m.f[j, v] for j in nodes if j != v)
            return in_flow - out_flow == 1
    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_root)

    # Total edges must be exactly n-1 (tree)
    def edge_count_rule(m):
        return sum(m.x[i, j] for (i, j) in edges) == n - 1
    model.edge_count = pyo.Constraint(rule=edge_count_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible_or_failed"}