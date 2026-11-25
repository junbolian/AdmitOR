import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]

    # Directed arcs in the listed order
    arcs = [
        (0, 1), (1, 0),
        (0, 3), (3, 0),
        (0, 5), (5, 0),
        (0, 6), (6, 0),
        (0, 7), (7, 0),
        (1, 2), (2, 1),
        (1, 5), (5, 1),
        (1, 6), (6, 1),
        (2, 3), (3, 2),
        (2, 6), (6, 2),
        (3, 4), (4, 3),
        (4, 5), (5, 4),
        (4, 6), (6, 4),
        (4, 7), (7, 4),
        (5, 6), (6, 5),
        (5, 7), (7, 5),
        (6, 7), (7, 6),
    ]

    # Commodity data: (source, sink, demand)
    # Commodity 1: source 3, sink 7; Commodity 2: source 1, sink 5
    commodity_source = {1: 3, 2: 1}
    commodity_sink = {1: 7, 2: 5}
    commodity_demand = {1: demands[0], 2: demands[1]}

    cap = {arcs[i]: arc_capacities[i] for i in range(len(arcs))}
    cost = {arcs[i]: arc_unit_costs[i] for i in range(len(arcs))}

    model = pyo.ConcreteModel()

    model.NODES = pyo.RangeSet(0, num_nodes - 1)
    model.COMMODITIES = pyo.RangeSet(1, num_commodities)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.COMMODITIES, model.ARCS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            cost[(i, j)] * m.flow[k, (i, j)]
            for k in m.COMMODITIES
            for (i, j) in m.ARCS
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, i, j):
        return sum(m.flow[k, (i, j)] for k in m.COMMODITIES) <= cap[(i, j)]
    model.capacity_con = pyo.Constraint(model.ARCS, rule=capacity_rule)

    def balance_rule(m, k, node):
        inflow = sum(m.flow[k, (i, node)] for (i, j) in m.ARCS if j == node)
        outflow = sum(m.flow[k, (node, j)] for (i, j) in m.ARCS if i == node)
        src = commodity_source[k]
        snk = commodity_sink[k]
        dem = commodity_demand[k]
        if node == src:
            return outflow - inflow == dem
        elif node == snk:
            return inflow - outflow == dem
        else:
            return inflow - outflow == 0
    model.balance_con = pyo.Constraint(model.COMMODITIES, model.NODES, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}