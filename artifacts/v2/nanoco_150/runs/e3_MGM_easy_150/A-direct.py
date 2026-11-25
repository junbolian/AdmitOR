import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural data: 11 teams (0..10) and 16 undirected compatibility edges.
    edges = [
        (0, 1), (0, 4), (0, 5), (0, 7),
        (1, 6), (1, 10),
        (2, 4), (2, 7), (2, 10),
        (3, 6),
        (4, 5), (4, 6), (4, 8),
        (5, 7),
        (6, 9),
        (7, 8),
    ]

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[e] for e in m.E)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Each node incident to at most one selected edge
    incidence = {v: [] for v in range(11)}
    for (u, w) in edges:
        incidence[u].append((u, w))
        incidence[w].append((u, w))

    def node_rule(m, v):
        inc = incidence[v]
        if not inc:
            return pyo.Constraint.Skip
        return sum(m.x[e] for e in inc) <= 1

    model.node_limit = pyo.Constraint(range(11), rule=node_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}