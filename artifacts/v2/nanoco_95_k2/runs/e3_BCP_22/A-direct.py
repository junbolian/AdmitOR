import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])

    edges = [
        (0, 1, params["safety_buffer_0_1"]),
        (0, 7, params["safety_buffer_0_7"]),
        (1, 4, params["safety_buffer_1_4"]),
        (1, 7, params["safety_buffer_1_7"]),
        (4, 5, params["safety_buffer_4_5"]),
    ]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.edge_set = pyo.RangeSet(0, len(edges) - 1)

    # Upper bound for slots
    max_buffer = max(d for _, _, d in edges)
    ub = num_nodes * (max_buffer + 1)

    model.x = pyo.Var(model.nodes, domain=pyo.NonNegativeIntegers, bounds=(0, ub))
    model.z = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, ub))

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    # Each aircraft slot bounded by z
    model.slot_bound = pyo.Constraint(
        model.nodes, rule=lambda m, i: m.x[i] <= m.z
    )

    # Conflict separation constraints with big-M linearization
    big_m = ub + max_buffer + 1

    def sep_rule(m, e):
        u, v, d = edges[e]
        return m.x[u] - m.x[v] >= d - big_m * m.bin_uv[e]

    def sep_rule_rev(m, e):
        u, v, d = edges[e]
        return m.x[v] - m.x[u] >= d - big_m * (1 - m.bin_uv[e])

    model.bin_uv = pyo.Var(model.edge_set, domain=pyo.Binary)
    model.sep_pos = pyo.Constraint(model.edge_set, rule=sep_rule)
    model.sep_neg = pyo.Constraint(model.edge_set, rule=sep_rule_rev)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}