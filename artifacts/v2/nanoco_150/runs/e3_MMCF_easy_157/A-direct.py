import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(10))
    undirected_edges = [
        (0, 1), (0, 5), (0, 7), (0, 8), (0, 9),
        (1, 2), (2, 3), (2, 9), (3, 4), (4, 5),
        (5, 6), (6, 7), (6, 9), (7, 8), (8, 9),
    ]

    arcs = []
    for u, v in undirected_edges:
        arcs.append((u, v))
        arcs.append((v, u))

    def edge_key(u, v):
        # Param keys use zero-padded two-digit node indices, e.g. "01_10", "05_50"
        a, b = (u, v) if u < v else (v, u)
        return f"{a:02d}_{b:02d}"

    capacity = {}
    cost = {}
    for (u, v) in arcs:
        k = edge_key(u, v)
        capacity[(u, v)] = params[f"arc_capacity_{k}"]
        cost[(u, v)] = params[f"unit_cost_{k}"]

    flows = [
        {"id": 1, "src": 5, "dst": 4, "demand": params["demand_flow1_5_to_4"]},
        {"id": 2, "src": 3, "dst": 0, "demand": params["demand_flow2_3_to_0"]},
    ]
    flow_ids = [f["id"] for f in flows]
    demand = {f["id"]: f["demand"] for f in flows}
    src = {f["id"]: f["src"] for f in flows}
    dst = {f["id"]: f["dst"] for f in flows}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.FLOWS = pyo.Set(initialize=flow_ids)
    model.NODES = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.FLOWS, model.ARCS, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    out_arcs = {n: [(u, v) for (u, v) in arcs if u == n] for n in nodes}
    in_arcs = {n: [(u, v) for (u, v) in arcs if v == n] for n in nodes}

    def flow_balance_rule(m, k, n):
        out_flow = sum(m.x[k, a] for a in out_arcs[n])
        in_flow = sum(m.x[k, a] for a in in_arcs[n])
        if n == src[k]:
            return out_flow - in_flow == demand[k]
        elif n == dst[k]:
            return out_flow - in_flow == -demand[k]
        else:
            return out_flow - in_flow == 0.0

    model.flow_balance = pyo.Constraint(
        model.FLOWS, model.NODES, rule=flow_balance_rule
    )

    def capacity_rule(m, a):
        return sum(m.x[k, a] for k in flow_ids) <= capacity[a]

    model.capacity_constraint = pyo.Constraint(model.ARCS, rule=capacity_rule)

    def utilization_rule(m, a):
        return sum(m.x[k, a] for k in flow_ids) <= m.z * capacity[a]

    model.utilization_constraint = pyo.Constraint(model.ARCS, rule=utilization_rule)

    model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}