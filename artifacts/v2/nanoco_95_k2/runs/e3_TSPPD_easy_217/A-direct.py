import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = params["num_nodes"]
    p = params["num_pairs"]

    nodes = list(range(n))
    # pickup node i -> delivery node i + p  (pairs occupy consecutive blocks)
    pickup = list(range(1, p + 1))
    delivery = list(range(p + 1, 2 * p + 1))

    model = pyo.ConcreteModel()

    # x[i,j] = 1 if arc i->j is used
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # forbid self loops
    for i in nodes:
        model.x[i, i].fix(0)

    # each node has exactly one outgoing and one incoming arc
    model.out_flow = pyo.Constraint(
        nodes, rule=lambda m, i: sum(m.x[i, j] for j in nodes) == 1
    )
    model.in_flow = pyo.Constraint(
        nodes, rule=lambda m, j: sum(m.x[i, j] for i in nodes) == 1
    )

    # precedence: pickup must precede its delivery
    # order variables u[i] in [1, n-1] for non-hub nodes
    nonhub = list(range(1, n))
    model.u = pyo.Var(nonhub, bounds=(1, n - 1))

    def prec_rule(m, k):
        return m.u[k] + 1 <= m.u[k + p]

    model.precedence = pyo.Constraint(pickup, rule=prec_rule)

    # MTZ subtour elimination for non-hub nodes
    def mtz_rule(m, i, j):
        if i == 0 or j == 0 or i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1

    model.subtour = pyo.Constraint(nodes, nodes, rule=mtz_rule)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for i in nodes for j in nodes)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}