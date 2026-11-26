import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    caps = params["arc_capacities"]
    n = 8
    source = 0
    sink = 7

    model = pyo.ConcreteModel()

    # Directed arcs with positive capacity
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j and caps[i][j] > 0:
                arcs.append((i, j))
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.capacity = pyo.Param(model.ARCS, initialize=lambda m, i, j: caps[i][j])

    def cap_rule(m, i, j):
        return m.flow[i, j] <= m.capacity[i, j]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    model.nodes = pyo.Set(initialize=range(n))

    def balance_rule(m, k):
        out_flow = sum(m.flow[a, j] for (a, j) in m.ARCS if a == k)
        in_flow = sum(m.flow[i, b] for (i, b) in m.ARCS if b == k)
        if k == source:
            return out_flow - in_flow >= 0
        elif k == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0
    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def obj_rule(m):
        return sum(m.flow[a, j] for (a, j) in m.ARCS if a == source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}