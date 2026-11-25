import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    required_edges = [(0, 3), (1, 7), (2, 8), (3, 7), (4, 5), (4, 6), (5, 7), (5, 8)]
    optional_edges = [(2, 3), (3, 5)]

    dist = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                dist[(i, j)] = 0.0
            else:
                key = "dist_%d_%d" % (i, j)
                if key in params:
                    dist[(i, j)] = float(params[key])
                else:
                    dist[(i, j)] = float(params["dist_%d_%d" % (min(i, j), max(i, j))])

    dist[(2, 4)] = float(params["dist_2_4_asym"])
    dist[(4, 2)] = float(params["dist_4_2_asym"])

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers, bounds=(0, None))

    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[(i, j)] for (i, j) in m.ARCS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, j):
        inflow = sum(m.x[(i, j)] for i in m.NODES if i != j)
        outflow = sum(m.x[(j, k)] for k in m.NODES if k != j)
        return inflow == outflow
    model.flow = pyo.Constraint(model.NODES, rule=flow_rule)

    def depot_rule(m):
        return sum(m.x[(0, j)] for j in m.NODES if j != 0) >= 1
    model.depot_rule = pyo.Constraint(rule=depot_rule)

    req_arcs = []
    for (u, v) in required_edges:
        req_arcs.append((u, v))
        req_arcs.append((v, u))

    def req_arc_rule(m, a, b):
        return m.x[(a, b)] + m.x[(b, a)] >= 1
    model.req_arc = pyo.Constraint(required_edges, rule=req_arc_rule)

    model.VARCS = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    model.f = pyo.Var(model.VARCS, model.NODES, domain=pyo.NonNegativeReals)

    def f_bound_rule(m, a, b, k):
        return m.f[(a, b), k] <= m.x[(a, b)]
    model.f_bound = pyo.Constraint(model.VARCS, model.NODES, rule=f_bound_rule)

    def f_balance_rule(m, k):
        outflow = sum(m.x[(k, j)] for j in m.NODES if j != k)
        inflow = sum(m.x[(i, k)] for i in m.NODES if i != k)
        net = outflow - inflow
        f_out = sum(m.f[(k, b), k] for b in m.NODES if b != k)
        f_in = sum(m.f[(a, k), k] for a in m.NODES if a != k)
        return (f_out - f_in) == net
    model.f_balance = pyo.Constraint(model.NODES, rule=f_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}