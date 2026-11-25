import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    supplies = params["supplies"]
    coordinates = params["coordinates"]

    num_nodes = 10
    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6), (5, 9),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]
    arc_index = list(range(len(arcs)))
    nodes = list(range(num_nodes))

    cap = {arc_index[k]: capacities[k] for k in arc_index}
    cost = {arc_index[k]: costs[k] for k in arc_index}
    tail = {arc_index[k]: arcs[k][0] for k in arc_index}
    head = {arc_index[k]: arcs[k][1] for k in arc_index}
    supply = {i: supplies[i] for i in nodes}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_index)
    model.NODES = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def capacity_rule(md, a):
        return md.flow[a] <= cap[a]

    model.capacity_con = pyo.Constraint(model.ARCS, rule=capacity_rule)

    def flow_balance_rule(md, i):
        inflow = sum(md.flow[a] for a in arc_index if head[a] == i)
        outflow = sum(md.flow[a] for a in arc_index if tail[a] == i)
        return inflow - outflow == -supply[i]

    model.balance_con = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def obj_rule(md):
        return sum(cost[a] * md.flow[a] for a in arc_index)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}