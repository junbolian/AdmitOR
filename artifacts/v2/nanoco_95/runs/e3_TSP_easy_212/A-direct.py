import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = int(params["num_nodes"])

    model = pyo.ConcreteModel()

    nodes = list(range(n))
    clients = [i for i in nodes if i != 0]

    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)
    model.u = pyo.Var(clients, domain=pyo.NonNegativeReals, bounds=(1, n - 1))

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j]
                   for i in nodes for j in nodes if i != j)
    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1
    model.out_degree = pyo.Constraint(nodes, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1
    model.in_degree = pyo.Constraint(nodes, rule=in_rule)

    def subtour_rule(m, i, j):
        if i == j or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2
    model.subtour = pyo.Constraint(clients, nodes, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}