import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
from itertools import combinations


def solve(params):
    N = 16
    root = 0
    port_limit = params["splitter_port_limit"]

    dist = {}
    for i in range(N):
        for j in range(i + 1, N):
            d = params["dist_%d_%d" % (i, j)]
            dist[(i, j)] = d
            dist[(j, i)] = d

    edges = list(combinations(range(N), 2))
    ordered = [(i, j) for (i, j) in edges] + [(j, i) for (i, j) in edges]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.Binary)
    model.f = pyo.Var(ordered, domain=pyo.NonNegativeReals)

    # Link flow to edge selection (single bounded constraint per arc)
    def link_rule(m, i, j):
        e = (i, j) if i < j else (j, i)
        return m.f[i, j] <= (N - 1) * m.x[e]

    model.link = pyo.Constraint(ordered, rule=link_rule)

    # Conservation: root is source of N-1 units
    def balance_rule(m, i):
        inflow = sum(m.f[j, i] for (j, k) in ordered if k == i)
        outflow = sum(m.f[i, j] for (j, k) in ordered if j == i)
        if i == root:
            return outflow - inflow == N - 1
        return outflow - inflow == -1

    model.balance = pyo.Constraint(range(N), rule=balance_rule)

    # Branch size limit on flow leaving root
    def branch_rule(m, c):
        return m.f[0, c] <= port_limit

    model.branch_limit = pyo.Constraint(range(1, N), rule=branch_rule)

    model.num_edges = pyo.Constraint(
        expr=sum(model.x[e] for e in edges) == N - 1
    )

    model.total_cost = pyo.Objective(
        expr=sum(dist[e] * model.x[e] for e in edges), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}