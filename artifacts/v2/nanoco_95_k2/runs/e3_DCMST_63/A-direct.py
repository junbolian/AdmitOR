import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["pipe_cost_matrix"]
    max_degree = params["max_degree_per_node"]

    N = len(cost)
    nodes = list(range(N))
    edges = [(i, j) for i in range(N) for j in range(i + 1, N)]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    # Degree constraints: each node has at most max_degree connections
    def degree_rule(m, i):
        return sum(m.x[min(i, j), max(i, j)] for j in nodes if j != i) <= max_degree
    model.degree_con = pyo.Constraint(model.nodes, rule=degree_rule)

    # Connectivity + acyclicity: a tree on N nodes has exactly N-1 edges
    def total_edges_rule(m):
        return sum(m.x[e] for e in m.edges) == N - 1
    model.total_edges_con = pyo.Constraint(rule=total_edges_rule)

    # Objective: minimize total installation cost
    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in edges)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}