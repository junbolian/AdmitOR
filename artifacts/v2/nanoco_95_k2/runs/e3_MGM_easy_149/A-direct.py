import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 5),
        (3, 4), (3, 7),
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    nodes = list(range(8))

    model = pyo.ConcreteModel()
    model.EDGES = pyo.Set(initialize=edges, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    def node_rule(mdl, n):
        incident = [e for e in edges if n in e]
        if not incident:
            return pyo.Constraint.Skip
        return sum(mdl.x[e] for e in incident) <= 1

    def obj_rule(mdl):
        return sum(mdl.x[e] for e in mdl.EDGES)

    model.node_limit = pyo.Constraint(model.NODES, rule=node_rule)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}