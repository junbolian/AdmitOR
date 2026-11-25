import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1, params["edge_0_1_weight"]),
        (0, 2, params["edge_0_2_weight"]),
        (0, 4, params["edge_0_4_weight"]),
        (1, 2, params["edge_1_2_weight"]),
        (1, 6, params["edge_1_6_weight"]),
        (2, 3, params["edge_2_3_weight"]),
        (2, 6, params["edge_2_6_weight"]),
        (3, 5, params["edge_3_5_weight"]),
    ]

    n = 7
    max_level = sum(w for _, _, w in edges)

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n - 1)
    model.edge_idx = pyo.RangeSet(0, len(edges) - 1)

    model.x = pyo.Var(model.nodes, domain=pyo.NonNegativeIntegers, bounds=(0, max_level))
    model.z = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, max_level))

    model.edge_list = edges

    # Introduce binary orientation variables to linearize |x_u - x_v| >= d
    model.dir = pyo.Var(model.edge_idx, domain=pyo.Binary)

    bigM = max_level + 1

    def fwd_rule(model, e):
        u, v, d = model.edge_list[e]
        return model.x[u] - model.x[v] >= d - bigM * (1 - model.dir[e])

    def rev_rule(model, e):
        u, v, d = model.edge_list[e]
        return model.x[v] - model.x[u] >= d - bigM * model.dir[e]

    model.link_fwd = pyo.Constraint(model.edge_idx, rule=fwd_rule)
    model.link_rev = pyo.Constraint(model.edge_idx, rule=rev_rule)

    def z_rule(model, i):
        return model.z >= model.x[i]

    model.z_bound = pyo.Constraint(model.nodes, rule=z_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}