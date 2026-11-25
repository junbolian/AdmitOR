import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3]
    ordered_pairs = [
        (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 3),
        (3, 0), (3, 1), (3, 2),
    ]

    dist = {
        (i, j): params["distance_{}_{}".format(i, j)]
        for (i, j) in ordered_pairs
    }

    big_M = params["big_M"]
    num_facilities = params["num_facilities"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.P = pyo.Set(initialize=ordered_pairs, dimen=2)

    model.Nodes = pyo.Var(model.N, domain=pyo.Binary)
    model.PairSelection = pyo.Var(model.P, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.Reals)

    # Exactly num_facilities selected
    model.facility_count = pyo.Constraint(
        expr=sum(model.Nodes[i] for i in nodes) == num_facilities
    )

    # Pair selection logic
    def pair_ub_i(m, i, j):
        return m.PairSelection[i, j] <= m.Nodes[i]

    def pair_ub_j(m, i, j):
        return m.PairSelection[i, j] <= m.Nodes[j]

    def pair_lb(m, i, j):
        return m.PairSelection[i, j] >= m.Nodes[i] + m.Nodes[j] - 1

    model.pair_ub_i = pyo.Constraint(model.P, rule=pair_ub_i)
    model.pair_ub_j = pyo.Constraint(model.P, rule=pair_ub_j)
    model.pair_lb = pyo.Constraint(model.P, rule=pair_lb)

    # Distance constraints
    def distance_rule(m, i, j):
        return m.MinDistance <= dist[(i, j)] + big_M * (1 - m.PairSelection[i, j])

    model.distance_con = pyo.Constraint(model.P, rule=distance_rule)

    model.obj = pyo.Objective(expr=model.MinDistance, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}