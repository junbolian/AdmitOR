import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    users = list(range(7))
    freqs = list(range(5))

    edges = [
        (0, 0), (0, 2), (0, 3),
        (1, 4),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 4),
        (5, 0),
    ]

    edges_by_user = {u: [] for u in users}
    edges_by_freq = {f: [] for f in freqs}
    for (u, f) in edges:
        edges_by_user[u].append((u, f))
        edges_by_freq[f].append((u, f))

    model = pyo.ConcreteModel()

    model.users = pyo.Set(initialize=users)
    model.freqs = pyo.Set(initialize=freqs)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def user_rule(m, u):
        terms = [m.x[e] for e in edges_by_user[u]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1
    model.user_con = pyo.Constraint(model.users, rule=user_rule)

    def freq_rule(m, f):
        terms = [m.x[e] for e in edges_by_freq[f]]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1
    model.freq_con = pyo.Constraint(model.freqs, rule=freq_rule)

    def obj_rule(m):
        return sum(m.x[e] for e in m.edges)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}