import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_list = [
        (0, 1), (1, 0), (0, 5), (5, 0), (0, 7), (7, 0), (0, 8), (8, 0),
        (0, 9), (9, 0), (1, 2), (2, 1), (2, 3), (3, 2), (2, 9), (9, 2),
        (3, 4), (4, 3), (4, 5), (5, 4), (5, 6), (6, 5), (6, 7), (7, 6),
        (6, 9), (9, 6), (7, 8), (8, 7), (8, 9), (9, 8),
    ]
    commodities = [1, 2]
    sources = {1: 5, 2: 3}
    sinks = {1: 4, 2: 0}
    demands = {1: params["demand_commodity_1"], 2: params["demand_commodity_2"]}

    capacity = {arc_list[i]: params["arc_capacity"][i] for i in range(len(arc_list))}
    cost = {arc_list[i]: params["arc_cost"][i] for i in range(len(arc_list))}

    nodes = list(range(10))

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arc_list, dimen=2)
    model.COMM = pyo.Set(initialize=commodities)
    model.NODE = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.COMM, model.ARC, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[a] * m.flow[k, a] for k in commodities for a in arc_list)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def conserve_rule(m, k, n):
        out_flow = sum(m.flow[k, a] for a in arc_list if a[0] == n)
        in_flow = sum(m.flow[k, a] for a in arc_list if a[1] == n)
        if n == sources[k]:
            return out_flow - in_flow == demands[k]
        elif n == sinks[k]:
            return in_flow - out_flow == demands[k]
        else:
            return out_flow - in_flow == 0

    model.conserve = pyo.Constraint(model.COMM, model.NODE, rule=conserve_rule)

    def cap_rule(m, i, j):
        return sum(m.flow[k, (i, j)] for k in commodities) <= capacity[(i, j)]

    model.cap = pyo.Constraint(model.ARC, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}