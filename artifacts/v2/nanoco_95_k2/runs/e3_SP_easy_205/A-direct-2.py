import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supply = params["node_supply"]

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4), (3, 7),
        (4, 5),
        (5, 6), (5, 7),
        (6, 7), (6, 8),
        (7, 8),
    ]
    nodes = list(range(9))
    arc_index = list(range(len(arcs)))

    cost = {i: arc_costs[i] for i in arc_index}
    cap = {i: arc_capacities[i] for i in arc_index}
    sup = {n: node_supply[n] for n in nodes}
    head = {i: arcs[i][0] for i in arc_index}
    tail = {i: arcs[i][1] for i in arc_index}

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arc_index)
    model.NODE = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals, bounds=(0, None))

    def cap_rule(m, a):
        return m.x[a] <= cap[a]
    model.cap_con = pyo.Constraint(model.ARC, rule=cap_rule)

    def flow_rule(m, n):
        inflow = sum(m.x[a] for a in arc_index if tail[a] == n)
        outflow = sum(m.x[a] for a in arc_index if head[a] == n)
        return outflow - inflow == sup[n]
    model.flow_con = pyo.Constraint(model.NODE, rule=flow_rule)

    def obj_rule(m):
        return sum(cost[a] * m.x[a] for a in arc_index)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}