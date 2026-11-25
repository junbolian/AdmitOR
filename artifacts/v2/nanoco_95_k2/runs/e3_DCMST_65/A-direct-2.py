import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]

    n = len(cost_matrix)
    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i < j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, within=pyo.Binary)
    # flow variables for single-commodity flow (rooted at node 0) to rule out cycles
    model.f = pyo.Var(edges, within=pyo.NonNegativeReals)

    edge_set = set(edges)

    def edge_var(a, b):
        if a < b:
            return model.x[(a, b)]
        return model.x[(b, a)]

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[(i, j)] for (i, j) in edges),
        sense=pyo.minimize,
    )

    # exactly n-1 edges (tree)
    model.tree_size = pyo.Constraint(expr=sum(model.x[e] for e in edges) == n - 1)

    # degree constraint at every node
    model.degree_con = pyo.ConstraintList()
    for v in nodes:
        model.degree_con.add(
            sum(model.x[e] for e in edges if e[0] == v or e[1] == v) <= max_degree
        )

    # single commodity flow: root sends n-1 units; each non-root consumes 1
    # f on edge = amount of flow from root traversing that edge
    inflow = {v: [] for v in nodes}
    outflow = {v: [] for v in nodes}
    for (i, j) in edges:
        outflow[i].append(model.f[(i, j)])
        inflow[j].append(model.f[(i, j)])

    model.flow_con = pyo.ConstraintList()
    for v in nodes:
        out_sum = sum(outflow[v])
        in_sum = sum(inflow[v])
        if v == 0:
            model.flow_con.add(out_sum - in_sum == n - 1)
        else:
            model.flow_con.add(in_sum - out_sum == 1)

    # capacity linking: flow only along chosen edges
    model.link = pyo.ConstraintList()
    for (i, j) in edges:
        model.link.add(model.f[(i, j)] <= (n - 1) * model.x[(i, j)])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}