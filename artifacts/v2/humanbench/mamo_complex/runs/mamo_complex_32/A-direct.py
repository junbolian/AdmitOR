import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    arcs = []
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = "capacity_{}_{}".format(i, j)
            if key in params:
                arcs.append((i, j))

    capacity = {arc: params["capacity_{}_{}".format(arc[0], arc[1])] for arc in arcs}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= capacity[(i, j)]
    model.cap = pyo.Constraint(model.arcs, rule=cap_rule)

    def flow_balance_rule(m, i):
        inflow = sum(m.flow[j, i] for (j, k) in arcs if k == i)
        outflow = sum(m.flow[i, j] for (k, j) in arcs if k == i)
        if i == source:
            return outflow - inflow >= 0
        if i == sink:
            return inflow - outflow >= 0
        return outflow - inflow == 0

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    model.objective = pyo.Objective(
        expr=sum(model.flow[source, j] for (k, j) in arcs if k == source)
        - sum(model.flow[j, source] for (j, k) in arcs if k == source),
        sense=pyo.maximize,
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}