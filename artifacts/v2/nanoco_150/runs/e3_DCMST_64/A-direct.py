import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 12
    edges = [(i, j) for i in range(1, N + 1) for j in range(i + 1, N + 1)]

    cost = {}
    for (i, j) in edges:
        name = "cost_%d_%d" % (i, j) if i >= 10 or j >= 10 else "cost_%d%d" % (i, j)
        cost[(i, j)] = params[name]

    model = pyo.ConcreteModel()
    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.nodes = pyo.RangeSet(1, N)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in edges),
        sense=pyo.minimize
    )

    def degree_rule(m, n):
        return sum(m.x[(i, j)] for (i, j) in edges if i == n or j == n) <= params["max_degree"]
    model.degree_con = pyo.Constraint(model.nodes, rule=degree_rule)

    def connectivity_rule(m):
        return sum(m.x[(i, j)] for (i, j) in edges) == N - 1
    model.connectivity_con = pyo.Constraint(rule=connectivity_rule)

    # subtour elimination via flow: root = 1, f[i,j] >= 0
    model.f = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def flow_balance_rule(m, n):
        out_flow = sum(m.f[(i, j)] for (i, j) in edges if i == n)
        in_flow = sum(m.f[(i, j)] for (i, j) in edges if j == n)
        if n == 1:
            return out_flow - in_flow == N - 1
        else:
            return in_flow - out_flow == 1
    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def flow_capacity_rule(m, i, j):
        return m.f[(i, j)] <= (N - 1) * m.x[(i, j)]
    model.flow_capacity = pyo.Constraint(model.edges, rule=flow_capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}