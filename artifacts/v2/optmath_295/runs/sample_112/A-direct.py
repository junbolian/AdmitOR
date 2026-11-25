import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distances = params["distances"]
    num_selected = params["num_selected"]
    num_nodes = params["num_nodes"]

    # Ordered pairs in the problem order
    pairs = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 0), (1, 2), (1, 3), (1, 4),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 0), (4, 1), (4, 2), (4, 3),
    ]
    dist_map = {pairs[i]: distances[i] for i in range(len(pairs))}

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.y = pyo.Var(model.nodes, domain=pyo.Binary)
    model.z = pyo.Var(model.pairs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(dist_map[(i, j)] * m.z[i, j] for (i, j) in m.pairs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def select_rule(m):
        return sum(m.y[i] for i in m.nodes) == num_selected
    model.select_con = pyo.Constraint(rule=select_rule)

    def link_rule(m, i, j):
        return m.z[i, j] <= m.y[i]
    model.link_i = pyo.Constraint(model.pairs, rule=link_rule)

    def link2_rule(m, i, j):
        return m.z[i, j] <= m.y[j]
    model.link_j = pyo.Constraint(model.pairs, rule=link2_rule)

    def link3_rule(m, i, j):
        return m.z[i, j] >= m.y[i] + m.y[j] - 1
    model.link_both = pyo.Constraint(model.pairs, rule=link3_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}