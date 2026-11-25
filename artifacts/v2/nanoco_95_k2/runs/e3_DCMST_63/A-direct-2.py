import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["pipe_cost_matrix"]
    max_degree = params["max_degree_per_node"]

    n = len(cost)
    nodes = list(range(n))

    # Single-commodity flow formulation for a Degree-Constrained Minimum
    # Spanning Tree (DCMST). Node 0 is the designated root.
    # y[i,j] = 1 if edge (i,j) is in the tree
    # f[i,j] = flow from i to j (directed), used to enforce connectivity
    #           and to prohibit subtours/cycles.
    root = 0

    # Build the edge list (undirected, i < j)
    edges = [(i, j) for i in nodes for j in nodes if i < j]

    # Directed arcs (both orientations of each undirected edge)
    arcs = [(i, j) for (i, j) in edges] + [(j, i) for (i, j) in edges]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    # Binary edge selection variables
    model.y = pyo.Var(model.edges, domain=pyo.Binary)

    # Continuous flow variables on directed arcs
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Cap on flow: each non-root node supplies 1 unit; total demand = n - 1.
    total_demand = n - 1

    def obj_rule(m):
        return sum(cost[i][j] * m.y[i, j] for (i, j) in m.edges)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Exactly n - 1 edges for a spanning tree
    def edge_count_rule(m):
        return sum(m.y[i, j] for (i, j) in m.edges) == n - 1

    model.edge_count = pyo.Constraint(rule=edge_count_rule)

    # Degree constraint at each node
    def degree_rule(m, v):
        return sum(m.y[i, j] for (i, j) in m.edges if i == v or j == v) <= max_degree

    model.degree_con = pyo.Constraint(model.nodes, rule=degree_rule)

    # Flow conservation: root sends (n-1) units, every other node absorbs 1 unit.
    def flow_balance_rule(m, v):
        outflow = sum(m.f[v, u] for (a, b) in m.arcs for (v_, u) in [(a, b)] if a == v)
        inflow = sum(m.f[u, v] for (a, b) in m.arcs for (u, v_) in [(a, b)] if b == v)
        if v == root:
            return outflow - inflow == total_demand
        else:
            return inflow - outflow == 1

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    # Flow only allowed on selected edges (both directions)
    def flow_link_rule(m, i, j):
        return m.f[i, j] <= total_demand * m.y[min(i, j), max(i, j)]

    model.flow_link = pyo.Constraint(model.arcs, rule=flow_link_rule)

    # Root cannot receive flow (it is the source)
    def root_in_rule(m, j):
        return m.f[j, root] == 0

    model.root_in = pyo.Constraint(
        pyo.Set(initialize=[j for j in nodes if j != root]), rule=root_in_rule
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}