import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    score = {}
    for (i, j) in pairs:
        score[(i, j)] = params["pair_score_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    def obj_rule(m):
        return sum(score[(i, j)] * m.y[(i, j)] for (i, j) in pairs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def exactly_two_rule(m):
        return sum(m.x[i] for i in m.N) == 2

    model.exactly_two = pyo.Constraint(rule=exactly_two_rule)

    def link_rule(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    model.link1 = pyo.Constraint(model.P, rule=link_rule)

    def link2_rule(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    model.link2 = pyo.Constraint(model.P, rule=link2_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}