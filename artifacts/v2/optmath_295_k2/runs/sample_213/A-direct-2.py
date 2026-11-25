import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    K = params["selection_count"]

    weights = {}
    for (i, j) in pairs:
        weights[(i, j)] = params["weight_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.select = pyo.Var(model.NODES, domain=pyo.Binary)
    model.disp = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(weights[(i, j)] * m.disp[(i, j)] for (i, j) in m.PAIRS)

    model.total_dispersion = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.selection_limit = pyo.Constraint(
        expr=sum(model.select[i] for i in model.NODES) == K
    )

    def disp_upper_i(m, i, j):
        return m.disp[(i, j)] <= m.select[i]

    def disp_upper_j(m, i, j):
        return m.disp[(i, j)] <= m.select[j]

    def disp_lower(m, i, j):
        return m.disp[(i, j)] >= m.select[i] + m.select[j] - 1

    model.disp_upper_i = pyo.Constraint(model.PAIRS, rule=disp_upper_i)
    model.disp_upper_j = pyo.Constraint(model.PAIRS, rule=disp_upper_j)
    model.disp_lower = pyo.Constraint(model.PAIRS, rule=disp_lower)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}