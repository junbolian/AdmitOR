import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def flow_bound(m, i, j):
        key = "capacity_%d_%d" % (i, j)
        if key in params:
            return (0, params[key])
        return (0, 0)

    model.flow = pyo.Var(model.arcs, bounds=flow_bound)

    model.net_out = pyo.Var(within=pyo.NonNegativeReals)

    def flow_balance_rule(m, k):
        incoming = sum(m.flow[i, k] for i in nodes if i != k)
        outgoing = sum(m.flow[k, j] for j in nodes if j != k)
        if k == source:
            return outgoing - incoming == m.net_out
        elif k == sink:
            return incoming - outgoing == m.net_out
        else:
            return incoming - outgoing == 0

    model.balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}