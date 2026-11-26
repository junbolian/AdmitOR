import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    edges = [
        ('a', 'f'), ('a', 'e'), ('a', 'b'),
        ('b', 'g'), ('b', 'c'),
        ('c', 'h'), ('c', 'd'),
        ('d', 'i'), ('d', 'e'),
        ('e', 'j'),
        ('f', 'g'), ('f', 'h'), ('f', 'i'), ('f', 'j'),
        ('g', 'h'), ('g', 'i'), ('g', 'j'),
        ('h', 'i'), ('h', 'j'),
        ('i', 'j'),
    ]

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=letters)
    model.E = pyo.Set(initialize=edges, dimen=2)
    model.x = pyo.Var(model.V, domain=pyo.Binary)

    def edge_rule(mdl, u, v):
        return mdl.x[u] + mdl.x[v] >= 1
    model.edge_cover = pyo.Constraint(model.E, rule=edge_rule)

    model.obj = pyo.Objective(expr=sum(model.x[v] for v in model.V), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}