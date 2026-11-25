import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities_selected = params["num_facilities_selected"]
    big_M = params["big_M"]

    nodes = ["node_0", "node_1", "node_2", "node_3", "node_4"]
    dist = {
        ("node_0", "node_1"): 10.0,
        ("node_0", "node_2"): 20.0,
        ("node_0", "node_3"): 15.0,
        ("node_0", "node_4"): 25.0,
        ("node_1", "node_2"): 30.0,
        ("node_1", "node_3"): 12.0,
        ("node_1", "node_4"): 18.0,
        ("node_2", "node_3"): 22.0,
        ("node_2", "node_4"): 28.0,
        ("node_3", "node_4"): 14.0,
    }

    pairs = [(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.w = pyo.Var(model.pairs, domain=pyo.Binary)
    model.min_distance = pyo.Var(domain=pyo.NonNegativeReals)

    model.select_count = pyo.Constraint(
        expr=sum(model.x[n] for n in model.nodes) == num_facilities_selected
    )

    def min_dist_rule(m, a, b):
        return m.min_distance <= dist[(a, b)] + big_M * (1 - m.w[(a, b)])

    model.min_dist_cons = pyo.Constraint(model.pairs, rule=min_dist_rule)

    def w_upper_rule(m, a, b):
        return m.w[(a, b)] <= (m.x[a] + m.x[b]) / 2.0

    def w_lower_rule(m, a, b):
        return m.w[(a, b)] >= m.x[a] + m.x[b] - 1

    model.w_upper = pyo.Constraint(model.pairs, rule=w_upper_rule)
    model.w_lower = pyo.Constraint(model.pairs, rule=w_lower_rule)

    model.obj = pyo.Objective(expr=model.min_distance, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}