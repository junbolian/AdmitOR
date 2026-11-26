import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 8
    SRC = 0
    SNK = 7

    # Build directed capacity dictionary from params
    cap = {}

    # From node 0 to 1..6 and 7
    cap[(0, 1)] = params["capacity_0_1"]
    cap[(0, 2)] = params["capacity_0_2"]
    cap[(0, 3)] = params["capacity_0_3"]
    cap[(0, 4)] = params["capacity_0_4"]
    cap[(0, 5)] = params["capacity_0_5"]
    cap[(0, 6)] = params["capacity_0_6"]
    cap[(0, 7)] = params["capacity_0_7"]

    others = {
        1: [0, 2, 3, 4, 5, 6, 7],
        2: [0, 1, 3, 4, 5, 6, 7],
        3: [0, 1, 2, 4, 5, 6, 7],
        4: [0, 1, 2, 3, 5, 6, 7],
        5: [0, 1, 2, 3, 4, 6, 7],
        6: [0, 1, 2, 3, 4, 5, 7],
        7: [0, 1, 2, 3, 4, 5, 6],
    }

    for i in range(1, 8):
        vals = params["capacities_from_%d" % i]
        for idx, j in enumerate(others[i]):
            cap[(i, j)] = vals[idx]

    # Arcs with positive capacity
    arcs = [(i, j) for (i, j) in cap if i != j and cap[(i, j)] > 0]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=range(N))

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def _cap_rule(mdl, i, j):
        return mdl.flow[(i, j)] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=_cap_rule)

    # Flow conservation (all nodes except source and sink)
    def _cons_rule(mdl, k):
        if k == SRC or k == SNK:
            return pyo.Constraint.Skip
        inflow = sum(mdl.flow[(i, j)] for (i, j) in arcs if j == k)
        outflow = sum(mdl.flow[(i, j)] for (i, j) in arcs if i == k)
        return inflow == outflow
    model.cons_con = pyo.Constraint(model.NODES, rule=_cons_rule)

    # Objective: maximize net flow out of source
    model.net_out = pyo.Expression(
        expr=sum(model.flow[(i, j)] for (i, j) in arcs if i == SRC)
        - sum(model.flow[(i, j)] for (i, j) in arcs if j == SRC)
    )

    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}