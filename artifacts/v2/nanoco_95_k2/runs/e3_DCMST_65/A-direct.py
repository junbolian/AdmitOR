import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]

    n = len(cost_matrix)
    nodes = list(range(n))

    # Build edge list for i < j
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    # Binary edge selection
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    # Flow variables (directed) for connectivity
    # Flow on directed arc (i,j) for each i != j
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    # Link flow to edge selection (symmetric x)
    def _link_rule(m, i, j):
        if i < j:
            return m.f[i, j] <= (n - 1) * m.x[i, j]
        else:
            return m.f[i, j] <= (n - 1) * m.x[j, i]

    model.link_con = pyo.Constraint(model.arcs, rule=_link_rule)

    # Flow conservation: root (node 0) sends n-1 units; each other node consumes 1
    def _flow_rule(m, k):
        if k == 0:
            outflow = sum(m.f[0, j] for j in nodes if j != 0)
            inflow = sum(m.f[i, 0] for i in nodes if i != 0)
            return outflow - inflow == n - 1
        else:
            inflow = sum(m.f[i, k] for i in nodes if i != k)
            outflow = sum(m.f[k, j] for j in nodes if j != k)
            return inflow - outflow == 1

    model.flow_con = pyo.Constraint(model.nodes, rule=_flow_rule)

    # Total edges = n - 1
    def _edge_count_rule(m):
        return sum(m.x[e] for e in m.edges) == n - 1

    model.edge_count_con = pyo.Constraint(rule=_edge_count_rule)

    # Degree constraint
    def _degree_rule(m, k):
        return sum(m.x[min(k, j), max(k, j)] for j in nodes if j != k) <= max_degree

    model.degree_con = pyo.Constraint(model.nodes, rule=_degree_rule)

    # Objective
    def _obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for (i, j) in m.edges)

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}