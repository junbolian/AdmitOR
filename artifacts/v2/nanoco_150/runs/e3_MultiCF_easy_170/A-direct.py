import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(9))
    edges = [
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7), (2, 3),
        (2, 6), (2, 7), (3, 4), (4, 5), (4, 6), (5, 6),
        (6, 7), (7, 8),
    ]
    arcs = []
    for u, v in edges:
        arcs.append((u, v))
        arcs.append((v, u))

    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    demand = {
        1: params["demand_commodity1"],
        2: params["demand_commodity2"],
    }
    source = {1: 3, 2: 6}
    sink = {1: 2, 2: 1}
    commodities = [1, 2]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.commodities = pyo.Set(initialize=commodities)

    model.flow = pyo.Var(model.commodities, model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(arc_cost[(i, j)] * m.flow[k, i, j]
                   for k in m.commodities for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, i, j):
        return sum(m.flow[k, i, j] for k in m.commodities) <= arc_capacity[(i, j)]

    model.capacity_con = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(m, k, n):
        outflow = sum(m.flow[k, n, j] for j in nodes if (n, j) in arcs)
        inflow = sum(m.flow[k, i, n] for i in nodes if (i, n) in arcs)
        if n == source[k]:
            return outflow - inflow == demand[k]
        elif n == sink[k]:
            return inflow - outflow == demand[k]
        else:
            return inflow - outflow == 0

    model.balance_con = pyo.Constraint(model.commodities, nodes, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}