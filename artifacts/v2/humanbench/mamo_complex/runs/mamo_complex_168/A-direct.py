import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    source = 0
    sink = 7

    # Build arc list from params (all i != j)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    # Capacity parameter read from params dict
    def cap_init(m, i, j):
        return params["capacity_{}_{}".format(i, j)]

    model.cap = pyo.Param(model.ARC, initialize=cap_init, within=pyo.NonNegativeReals)

    # Flow variables
    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(m, i, j):
        return m.flow[i, j] <= m.cap[i, j]

    model.cap_con = pyo.Constraint(model.ARC, rule=cap_rule)

    # Flow conservation: source out - in = F, sink in - out = F, others balanced
    model.F = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(m, v):
        out_flow = sum(m.flow[v, j] for j in nodes if (v, j) in m.ARC)
        in_flow = sum(m.flow[i, v] for i in nodes if (i, v) in m.ARC)
        if v == source:
            return out_flow - in_flow == m.F
        elif v == sink:
            return in_flow - out_flow == m.F
        else:
            return out_flow - in_flow == 0

    model.balance = pyo.Constraint(model.NODE, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.F, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}