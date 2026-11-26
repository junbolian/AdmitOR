import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = range(7)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    cap = {}
    for (i, j) in arcs:
        key = "capacity_{}_{}".format(i, j)
        if key in params:
            cap[(i, j)] = params[key]
        else:
            cap[(i, j)] = 0.0

    flow_arcs = [(i, j) for (i, j) in arcs if cap[(i, j)] > 0]

    model.flow = pyo.Var(flow_arcs, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[(i, j)] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(flow_arcs, rule=cap_rule)

    def balance_rule(m, k):
        inflow = sum(m.flow[(i, k)] for (i, j) in flow_arcs if j == k)
        outflow = sum(m.flow[(k, j)] for (i, j) in flow_arcs if i == k)
        if k == 0:
            return outflow - inflow >= 0
        elif k == 6:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance_con = pyo.Constraint(nodes, rule=balance_rule)

    def obj_rule(m):
        return sum(m.flow[(0, j)] for (i, j) in flow_arcs if i == 0) - \
               sum(m.flow[(i, 0)] for (i, j) in flow_arcs if j == 0)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}