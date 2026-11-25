import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    big_M = params["big_M"]

    nodes = [0, 1, 2, 3]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    distance = {
        (0, 1): params["distance_0_1"],
        (0, 2): params["distance_0_2"],
        (0, 3): params["distance_0_3"],
        (1, 0): params["distance_1_0"],
        (1, 2): params["distance_1_2"],
        (1, 3): params["distance_1_3"],
        (2, 0): params["distance_2_0"],
        (2, 1): params["distance_2_1"],
        (2, 3): params["distance_2_3"],
        (3, 0): params["distance_3_0"],
        (3, 1): params["distance_3_1"],
        (3, 2): params["distance_3_2"],
    }

    model = pyo.ConcreteModel()

    model.Nodes = pyo.Set(initialize=nodes)
    model.Pairs = pyo.Set(initialize=pairs, dimen=2)

    model.Select = pyo.Var(model.Nodes, domain=pyo.Binary)
    model.PairSelect = pyo.Var(model.Pairs, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    model.total_facilities = pyo.Constraint(
        expr=sum(model.Select[n] for n in model.Nodes) == num_facilities
    )

    def distance_rule(m, i, j):
        return m.MinDistance <= distance[(i, j)] + big_M * (1 - m.PairSelect[i, j])

    model.distance_links = pyo.Constraint(model.Pairs, rule=distance_rule)

    def pair_ub_i(m, i, j):
        return m.PairSelect[i, j] <= m.Select[i]

    def pair_ub_j(m, i, j):
        return m.PairSelect[i, j] <= m.Select[j]

    def pair_lb(m, i, j):
        return m.PairSelect[i, j] >= m.Select[i] + m.Select[j] - 1

    model.pair_ub_i = pyo.Constraint(model.Pairs, rule=pair_ub_i)
    model.pair_ub_j = pyo.Constraint(model.Pairs, rule=pair_ub_j)
    model.pair_lb = pyo.Constraint(model.Pairs, rule=pair_lb)

    model.obj = pyo.Objective(expr=model.MinDistance, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}