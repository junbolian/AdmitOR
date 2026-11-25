import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_costs = params["arc_costs"]
    commodity_sources = params["commodity_sources"]
    commodity_sinks = params["commodity_sinks"]
    commodity_demands = params["commodity_demands"]

    arcs = [
        (0, 1), (1, 0), (0, 4), (4, 0), (1, 2), (2, 1), (1, 5), (5, 1),
        (2, 3), (3, 2), (2, 6), (6, 2), (3, 4), (4, 3), (3, 9), (9, 3),
        (4, 5), (5, 4), (4, 6), (6, 4), (5, 6), (6, 5), (5, 7), (7, 5),
        (6, 7), (7, 6), (7, 8), (8, 7), (8, 9), (9, 8),
    ]
    num_nodes = 10
    num_commodities = 2

    model = pyo.ConcreteModel()

    arc_index = list(range(len(arcs)))
    model.arcs = pyo.Set(initialize=arc_index)
    model.commodities = pyo.Set(initialize=list(range(num_commodities)))
    model.nodes = pyo.Set(initialize=list(range(num_nodes)))

    arc_tail = {k: arcs[k][0] for k in arc_index}
    arc_head = {k: arcs[k][1] for k in arc_index}

    model.flow = pyo.Var(model.commodities, model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(arc_costs[k] * m.flow[c, k] for c in m.commodities for k in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # capacity sharing
    def cap_rule(m, k):
        return sum(m.flow[c, k] for c in m.commodities) <= arc_capacities[k]

    model.capacity = pyo.Constraint(model.arcs, rule=cap_rule)

    # flow conservation
    def balance_rule(m, c, n):
        outflow = sum(m.flow[c, k] for k in arc_index if arc_tail[k] == n)
        inflow = sum(m.flow[c, k] for k in arc_index if arc_head[k] == n)
        src = commodity_sources[c]
        snk = commodity_sinks[c]
        dem = commodity_demands[c]
        if n == src:
            return outflow - inflow == dem
        elif n == snk:
            return inflow - outflow == dem
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(model.commodities, model.nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}