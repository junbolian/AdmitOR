import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    N = len(dist)
    nodes = list(range(N))
    customers = list(range(1, N))

    model = pyo.ConcreteModel()

    # x[i,j] = 1 if arc i->j is used
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # u[i] = subtour elimination ordering variable (MTZ)
    model.u = pyo.Var(customers, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for i in nodes for j in nodes if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1

    model.out_cons = pyo.Constraint(nodes, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1

    model.in_cons = pyo.Constraint(nodes, rule=in_rule)

    # No self loops
    def no_self(m, i):
        return m.x[i, i] == 0

    model.self_cons = pyo.Constraint(nodes, rule=no_self)

    # MTZ subtour elimination
    def mtz_rule(m, i, j):
        if i != j and j != 0:
            return m.u[i] - m.u[j] + (N - 1) * m.x[i, j] <= N - 2
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(customers, nodes, rule=mtz_rule)

    # Ordering bounds
    def u_bound(m, i):
        return pyo.inequality(1, m.u[i], N - 1)

    model.u_bounds = pyo.Constraint(customers, rule=u_bound)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}