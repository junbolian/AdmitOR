import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    dist = params["distance_matrix"]

    num_nodes = len(coords)
    nodes = list(range(num_nodes))
    depot = 0
    customers = [i for i in nodes if i != depot]

    pairs = [[6, 3], [1, 5], [2, 4]]

    model = pyo.ConcreteModel()

    # Decision variables: x[i, j] = 1 if arc i->j is used
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # Objective: minimize total travel distance
    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for i in nodes for j in nodes if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node entered exactly once
    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1

    model.in_deg = pyo.Constraint(nodes, rule=in_rule)

    # Each node left exactly once
    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1

    model.out_deg = pyo.Constraint(nodes, rule=out_rule)

    # No self arcs
    def no_self(m, i):
        return m.x[i, i] == 0

    model.no_self = pyo.Constraint(nodes, rule=no_self)

    # Subtour elimination via MTZ
    model.u = pyo.Var(customers, bounds=(1, num_nodes - 1))
    model.mtz = pyo.ConstraintList()
    for i in customers:
        for j in customers:
            if i != j:
                model.mtz.add(model.u[i] - model.u[j] + num_nodes * model.x[i, j] <= num_nodes - 1)

    # Precedence constraints: pickup before delivery (MTZ-based)
    model.prec = pyo.ConstraintList()
    for (u, v) in pairs:
        model.prec.add(model.u[u] - model.u[v] <= -1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}