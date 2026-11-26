import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 9
    source = 0
    sink = 8

    arcs = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if i == source and j == sink:
                pass
            # arcs exist per problem: 0 -> 1..8 ; i in 1..8 -> j != 0 ; and 8 has outgoing except 0
            if i == source:
                arcs.append((i, j))
            else:
                if j == 0:
                    continue
                arcs.append((i, j))

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    cap = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["cap_%d_%d" % (i, j)]

    def cap_rule(md, i, j):
        return (0, cap[(i, j)])

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals,
                         bounds=cap_rule)

    def flow_balance(md, k):
        inflow = sum(md.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(md.flow[i, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance)

    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source),
        sense=pyo.maximize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}