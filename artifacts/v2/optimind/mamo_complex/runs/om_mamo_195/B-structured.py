# IR: {"sets":{"V":["a","b","c","d","e","f","g","h","i","j"],"E":[["a","b"],["b","c"],["c","d"],["d","e"],["e","a"],["a","f"],["b","g"],["c","h"],["d","i"],["e","j"],["f","g"],["f","h"],["f","i"],["f","j"],["g","h"],["g","i"],["g","j"],["h","i"],["h","j"],["i","j"]]},"params":{},"variables":{"x[v]":"binary; 1 iff vertex v is selected"},"constraints":["x[u] + x[v] >= 1 for every (u,v) in E"],"objective":"minimize sum(x[v] for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = list("abcdefghij")
    edges = [
        ("a", "b"),
        ("b", "c"),
        ("c", "d"),
        ("d", "e"),
        ("e", "a"),
        ("a", "f"),
        ("b", "g"),
        ("c", "h"),
        ("d", "i"),
        ("e", "j"),
        ("f", "g"),
        ("f", "h"),
        ("f", "i"),
        ("f", "j"),
        ("g", "h"),
        ("g", "i"),
        ("g", "j"),
        ("h", "i"),
        ("h", "j"),
        ("i", "j"),
    ]

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.selected = pyo.Var(model.vertices, domain=pyo.Binary)

    def cover_rule(instance, u, v):
        return instance.selected[u] + instance.selected[v] >= 1

    model.edge_coverage = pyo.Constraint(model.edges, rule=cover_rule)
    model.cover_size = pyo.Objective(
        expr=sum(model.selected[vertex] for vertex in model.vertices),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.cover_size))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}