import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
    caps = {
        (1, 2): params["cap_1_2"],
        (1, 3): params["cap_1_3"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (3, 4): params["cap_3_4"],
    }
    source, sink = 1, 4
    nodes = [1, 2, 3, 4]

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=edges, dimen=2)
    model.N = pyo.Set(initialize=nodes)

    model.f = pyo.Var(model.E, within=pyo.NonNegativeReals)
    model.flow = pyo.Var(within=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.f[i, j] <= caps[(i, j)]

    model.cap_con = pyo.Constraint(model.E, rule=cap_rule)

    # Flow conservation at intermediate nodes
    int_nodes = [2, 3]

    def cons_rule(m, k):
        inflow = sum(m.f[i, j] for (i, j) in edges if j == k)
        outflow = sum(m.f[i, j] for (i, j) in edges if i == k)
        return inflow == outflow

    model.conservation = pyo.Constraint(int_nodes, rule=cons_rule)

    # Source: net outflow equals total flow
    def src_rule(m):
        out = sum(m.f[i, j] for (i, j) in edges if i == source)
        inc = sum(m.f[i, j] for (i, j) in edges if j == source)
        return out - inc == m.flow

    model.source_con = pyo.Constraint(rule=src_rule)

    # Sink: net inflow equals total flow
    def snk_rule(m):
        inc = sum(m.f[i, j] for (i, j) in edges if j == sink)
        out = sum(m.f[i, j] for (i, j) in edges if i == sink)
        return inc - out == m.flow

    model.sink_con = pyo.Constraint(rule=snk_rule)

    model.obj = pyo.Objective(expr=model.flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}