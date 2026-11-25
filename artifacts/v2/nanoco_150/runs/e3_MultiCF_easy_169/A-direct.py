import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(10))
    undirected = [
        (0, 1), (0, 4), (1, 2), (1, 3), (1, 5), (1, 6), (2, 3), (3, 4),
        (4, 5), (5, 6), (5, 9), (6, 7), (7, 8), (7, 9), (8, 9),
    ]
    arcs = []
    for u, v in undirected:
        arcs.append((u, v))
        arcs.append((v, u))

    cap_list = params["arc_capacity"]
    cost_list = params["arc_cost"]
    d1 = params["commodity1_demand"]
    d2 = params["commodity2_demand"]

    capacity = {a: cap_list[i] for i, a in enumerate(arcs)}
    cost = {a: cost_list[i] for i, a in enumerate(arcs)}

    commodities = [1, 2]
    sources = {1: 1, 2: 7}
    sinks = {1: 4, 2: 9}
    demands = {1: d1, 2: d2}

    model = pyo.ConcreteModel()
    model.NODE = pyo.Set(initialize=nodes)
    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.COMM = pyo.Set(initialize=commodities)

    model.flow = pyo.Var(model.COMM, model.ARC, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[a] * m.flow[k, a] for k in m.COMM for a in m.ARC)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, a):
        return sum(m.flow[k, a] for k in m.COMM) <= capacity[a]
    model.cap = pyo.Constraint(model.ARC, rule=cap_rule)

    def flow_balance_rule(m, k, n):
        outflow = sum(m.flow[k, a] for a in m.ARC if a[0] == n)
        inflow = sum(m.flow[k, a] for a in m.ARC if a[1] == n)
        if n == sources[k]:
            return outflow - inflow == demands[k]
        elif n == sinks[k]:
            return outflow - inflow == -demands[k]
        else:
            return outflow - inflow == 0
    model.balance = pyo.Constraint(model.COMM, model.NODE, rule=flow_balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}