# IR: {"sets":{"N":"0..9","K":"0..1","A":[[0,1],[1,0],[0,4],[4,0],[1,2],[2,1],[1,5],[5,1],[2,3],[3,2],[2,6],[6,2],[3,4],[4,3],[3,9],[9,3],[4,5],[5,4],[4,6],[6,4],[5,6],[6,5],[5,7],[7,5],[6,7],[7,6],[7,8],[8,7],[8,9],[9,8]]},"params":{"arc_capacities":"nonnegative real[A], supplied arc order","arc_costs":"real[A], supplied arc order","commodity_sources":"N[K]","commodity_sinks":"N[K]","commodity_demands":"nonnegative real[K]"},"variables":{"flow[k,i,j]":"nonnegative real, k in K, (i,j) in A"},"constraints":["For every k,n: sum(flow[k,n,j] over outgoing arcs) - sum(flow[k,i,n] over incoming arcs) = commodity_demands[k] * (1[n=commodity_sources[k]] - 1[n=commodity_sinks[k]]).","For every (i,j): sum(flow[k,i,j] over k in K) <= arc_capacities[i,j]."],"objective":"Minimize sum(arc_costs[i,j] * flow[k,i,j] over k in K and (i,j) in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (1, 0), (0, 4), (4, 0),
        (1, 2), (2, 1), (1, 5), (5, 1),
        (2, 3), (3, 2), (2, 6), (6, 2),
        (3, 4), (4, 3), (3, 9), (9, 3),
        (4, 5), (5, 4), (4, 6), (6, 4),
        (5, 6), (6, 5), (5, 7), (7, 5),
        (6, 7), (7, 6), (7, 8), (8, 7),
        (8, 9), (9, 8),
    ]

    arc_capacities = params["arc_capacities"]
    arc_costs = params["arc_costs"]
    commodity_sources = params["commodity_sources"]
    commodity_sinks = params["commodity_sinks"]
    commodity_demands = params["commodity_demands"]

    outgoing = {
        node: [head for tail, head in arcs if tail == node]
        for node in range(10)
    }
    incoming = {
        node: [tail for tail, head in arcs if head == node]
        for node in range(10)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.commodities = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_capacities = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_costs = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.commodity_sources = pyo.Param(
        model.commodities,
        initialize={commodity: commodity_sources[commodity]
                    for commodity in range(2)},
        within=model.nodes,
    )
    model.commodity_sinks = pyo.Param(
        model.commodities,
        initialize={commodity: commodity_sinks[commodity]
                    for commodity in range(2)},
        within=model.nodes,
    )
    model.commodity_demands = pyo.Param(
        model.commodities,
        initialize={commodity: commodity_demands[commodity]
                    for commodity in range(2)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def flow_balance_rule(network, commodity, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[commodity, node, head]
                for head in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[commodity, tail, node]
                for tail in incoming[node]
            )
        )
        source = pyo.value(network.commodity_sources[commodity])
        sink = pyo.value(network.commodity_sinks[commodity])
        required_net_outflow = network.commodity_demands[commodity] * (
            int(node == source) - int(node == sink)
        )
        return net_outflow == required_net_outflow

    model.flow_balance = pyo.Constraint(
        model.commodities,
        model.nodes,
        rule=flow_balance_rule,
    )

    def shared_capacity_rule(network, tail, head):
        return (
            pyo.quicksum(
                network.flow[commodity, tail, head]
                for commodity in network.commodities
            )
            <= network.arc_capacities[tail, head]
        )

    model.shared_capacity = pyo.Constraint(
        model.arcs,
        rule=shared_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.arc_costs[tail, head] * model.flow[commodity, tail, head]
            for commodity in model.commodities
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}