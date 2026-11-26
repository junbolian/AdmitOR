import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7

    arcs = []
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j))

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def _cap_rule(m, i, j):
        return (0, params["cap_%d_%d" % (i, j)])

    model.f = pyo.Var(model.arcs, bounds=_cap_rule)

    def _balance_rule(m, k):
        out_flow = sum(m.f[i, j] for (i, j) in arcs if i == k)
        in_flow = sum(m.f[i, j] for (i, j) in arcs if j == k)
        if k == source:
            return (in_flow - out_flow) == -m.total_sent
        elif k == sink:
            return (in_flow - out_flow) == m.total_sent
        else:
            return (in_flow - out_flow) == 0

    model.total_sent = pyo.Expression(expr=sum(model.f[source, j] for (i, j) in arcs if i == source))
    model.balance = pyo.Constraint(nodes, rule=_balance_rule)

    model.obj = pyo.Objective(expr=model.total_sent, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}