import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(5)
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    weight = {
        (0, 1): params["weight_0_1"],
        (0, 2): params["weight_0_2"],
        (0, 3): params["weight_0_3"],
        (0, 4): params["weight_0_4"],
        (1, 0): params["weight_1_0"],
        (1, 2): params["weight_1_2"],
        (1, 3): params["weight_1_3"],
        (1, 4): params["weight_1_4"],
        (2, 0): params["weight_2_0"],
        (2, 1): params["weight_2_1"],
        (2, 3): params["weight_2_3"],
        (2, 4): params["weight_2_4"],
        (3, 0): params["weight_3_0"],
        (3, 1): params["weight_3_1"],
        (3, 2): params["weight_3_2"],
        (3, 4): params["weight_3_4"],
        (4, 0): params["weight_4_0"],
        (4, 1): params["weight_4_1"],
        (4, 2): params["weight_4_2"],
        (4, 3): params["weight_4_3"],
    }

    # Effective dispersion for an unordered pair (i, j): combined directed weights
    pair_weight = {(i, j): weight[(i, j)] + weight[(j, i)] for (i, j) in pairs}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.y = pyo.Var(pairs, domain=pyo.Binary)

    model.selection = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == params["selection_count"]
    )

    def link_rule(mdl, i, j):
        return mdl.y[(i, j)] <= mdl.x[i]

    def link_rule2(mdl, i, j):
        return mdl.y[(i, j)] <= mdl.x[j]

    def link_rule3(mdl, i, j):
        return mdl.y[(i, j)] >= mdl.x[i] + mdl.x[j] - 1

    model.link_a = pyo.Constraint(pairs, rule=link_rule)
    model.link_b = pyo.Constraint(pairs, rule=link_rule2)
    model.link_c = pyo.Constraint(pairs, rule=link_rule3)

    model.obj = pyo.Objective(
        expr=sum(pair_weight[(i, j)] * model.y[(i, j)] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}