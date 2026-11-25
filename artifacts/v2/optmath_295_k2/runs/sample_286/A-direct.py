import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities_selected = params["num_facilities_selected"]
    big_M = params["big_M"]

    # Distance data between nodes (structural constants)
    nodes = ["node_0", "node_1", "node_2", "node_3", "node_4"]
    dist_data = {
        ("node_0", "node_1"): 10,
        ("node_0", "node_2"): 20,
        ("node_0", "node_3"): 30,
        ("node_0", "node_4"): 40,
        ("node_1", "node_2"): 15,
        ("node_1", "node_3"): 25,
        ("node_1", "node_4"): 35,
        ("node_2", "node_3"): 18,
        ("node_2", "node_4"): 28,
        ("node_3", "node_4"): 12,
    }

    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.NODES, domain=pyo.Binary)
    model.y = pyo.Var(model.PAIRS, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    model.distance = pyo.Param(model.PAIRS, initialize=dist_data)

    # Objective: maximize the minimum distance
    model.obj = pyo.Objective(expr=model.MinDistance, sense=pyo.maximize)

    # Exactly num_facilities_selected nodes selected
    model.select_constraint = pyo.Constraint(
        expr=sum(model.x[i] for i in model.NODES) == num_facilities_selected
    )

    # MinDistance <= distance(i,j) + big_M * (2 - x_i - x_j)
    def min_dist_rule(m, i, j):
        return m.MinDistance <= m.distance[i, j] + big_M * (2 - m.x[i] - m.x[j])

    model.min_dist_constraint = pyo.Constraint(model.PAIRS, rule=min_dist_rule)

    # Pairwise consistency
    def pair_consistency_rule(m, i, j):
        return m.y[i, j] <= m.x[i]

    def pair_consistency_rule2(m, i, j):
        return m.y[i, j] <= m.x[j]

    def pair_consistency_rule3(m, i, j):
        return m.y[i, j] >= m.x[i] + m.x[j] - 1

    model.pair_consistency_1 = pyo.Constraint(model.PAIRS, rule=pair_consistency_rule)
    model.pair_consistency_2 = pyo.Constraint(model.PAIRS, rule=pair_consistency_rule2)
    model.pair_consistency_3 = pyo.Constraint(model.PAIRS, rule=pair_consistency_rule3)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}