import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    # Build set of directed arcs with capacity > 0
    arcs = []
    cap_data = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            if i == source and j == sink:
                continue
            if i == sink:
                # sink has no outgoing arcs toward other nodes except defined back-edges
                pass
            key = "capacity_%d_%d" % (i, j)
            if key in params:
                c = params[key]
                if c > 0:
                    arcs.append((i, j))
                    cap_data[(i, j)] = c

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, cap_data[(i, j)]))

    # Flow conservation (with max-flow formulation: inflow = outflow except at source/sink)
    def flow_balance_rule(m, k):
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    # Objective: maximize flow out of source (equivalently into sink)
    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source),
        sense=pyo.maximize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}