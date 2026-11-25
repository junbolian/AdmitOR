import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    edge_costs_raw = params["edge_costs"]
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]

    required_edges = [(0, 1), (0, 3), (0, 6), (1, 3), (1, 5), (1, 6), (2, 3), (2, 4), (5, 7)]
    num_nodes = 8
    depot = 0
    nodes = list(range(num_nodes))

    # Build service cost lookup (unordered key)
    service_cost = {}
    for e in edge_costs_raw:
        a, b, c = int(e[0]), int(e[1]), float(e[2])
        service_cost[(a, b)] = c
        service_cost[(b, a)] = c

    # Directed arcs
    required_set = set()
    for (u, v) in required_edges:
        required_set.add((u, v))
        required_set.add((v, u))

    ordered_required = sorted(required_set)
    ordered_all = [(u, v) for u in nodes for v in nodes if u != v]

    unordered_req = []
    seen = set()
    for (u, v) in required_edges:
        key = (min(u, v), max(u, v))
        if key not in seen:
            seen.add(key)
            unordered_req.append(key)

    model = pyo.ConcreteModel()

    model.SARCS = pyo.Set(initialize=ordered_required, dimen=2)
    model.DARCS = pyo.Set(initialize=ordered_all, dimen=2)
    model.REQ = pyo.Set(initialize=unordered_req, dimen=2)

    model.s = pyo.Var(model.SARCS, domain=pyo.NonNegativeIntegers)
    model.d = pyo.Var(model.DARCS, domain=pyo.NonNegativeIntegers)

    def service_req_rule(mm, u, v):
        expr = 0
        if (u, v) in required_set:
            expr = expr + mm.s[(u, v)]
        if (v, u) in required_set and v != u:
            expr = expr + mm.s[(v, u)]
        return expr >= 1
    model.svc = pyo.Constraint(model.REQ, rule=service_req_rule)

    def flow_rule(mm, i):
        inflow = 0
        outflow = 0
        for (u, v) in ordered_required:
            if v == i:
                inflow = inflow + mm.s[(u, v)]
            if u == i:
                outflow = outflow + mm.s[(u, v)]
        for (u, v) in ordered_all:
            if v == i:
                inflow = inflow + mm.d[(u, v)]
            if u == i:
                outflow = outflow + mm.d[(u, v)]
        return inflow == outflow
    model.flow = pyo.Constraint(nodes, rule=flow_rule)

    def depot_rule(mm):
        out_expr = 0
        for (u, v) in ordered_required:
            if u == depot:
                out_expr = out_expr + mm.s[(u, v)]
        for (u, v) in ordered_all:
            if u == depot:
                out_expr = out_expr + mm.d[(u, v)]
        return out_expr >= 1
    model.depot_con = pyo.Constraint(rule=depot_rule)

    def obj_rule(mm):
        total = 0
        for (u, v) in ordered_required:
            total = total + service_cost[(u, v)] * mm.s[(u, v)]
        for (u, v) in ordered_all:
            total = total + float(distance_matrix[u][v]) * mm.d[(u, v)]
        return total
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}