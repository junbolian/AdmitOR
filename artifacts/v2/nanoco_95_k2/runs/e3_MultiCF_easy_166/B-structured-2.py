# IR: {"sets":{"N":"0..9","K":"0..1","A":[[0,1],[1,0],[0,4],[4,0],[1,2],[2,1],[1,5],[5,1],[2,3],[3,2],[2,6],[6,2],[3,4],[4,3],[3,9],[9,3],[4,5],[5,4],[4,6],[6,4],[5,6],[6,5],[5,7],[7,5],[6,7],[7,6],[7,8],[8,7],[8,9],[9,8]]},"params":{"arc_capacities":"nonnegative capacity per ordered arc","arc_costs":"real unit cost per ordered arc","commodity_sources":"source in N per commodity","commodity_sinks":"sink in N per commodity","commodity_demands":"nonnegative demand per commodity"},"variables":{"flow[k,i,j]":"NonNegativeReals for k in K, (i,j) in A"},"constraints":["For each k,n: sum(flow[k,n,j]) - sum(flow[k,i,n]) = commodity_demands[k] * (I[n=commodity_sources[k]] - I[n=commodity_sinks[k]])","For each (i,j): sum_k flow[k,i,j] <= arc_capacities[i,j]"],"objective":"minimize sum_(k,i,j) arc_costs[i,j] * flow[k,i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (1, 0), (0, 4), (4, 0), (1, 2), (2, 1),
        (1, 5), (5, 1), (2, 3), (3, 2), (2, 6), (6, 2),
        (3, 4), (4, 3), (3, 9), (9, 3), (4, 5), (5, 4),
        (4, 6), (6, 4), (5, 6), (6, 5), (5, 7), (7, 5),
        (6, 7), (7, 6), (7, 8), (8, 7), (8, 9), (9, 8),
    ]

    capacities = params["arc_capacities"]
    costs = params["arc_costs"]
    sources = params["commodity_sources"]
    sinks = params["commodity_sinks"]
    demands = params["commodity_demands"]

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
            arc: capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_costs = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.commodity_sources = pyo.Param(
        model.commodities,
        initialize={commodity: sources[commodity] for commodity in range(2)},
        within=model.nodes,
    )
    model.commodity_sinks = pyo.Param(
        model.commodities,
        initialize={commodity: sinks[commodity] for commodity in range(2)},
        within=model.nodes,
    )
    model.commodity_demands = pyo.Param(
        model.commodities,
        initialize={commodity: demands[commodity] for commodity in range(2)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.commodities, model.arcs, domain=pyo.NonNegativeReals
    )

    def flow_balance_rule(network, commodity, node):
        source = pyo.value(network.commodity_sources[commodity])
        sink = pyo.value(network.commodity_sinks[commodity])
        net_supply = network.commodity_demands[commodity] * (
            int(node == source) - int(node == sink)
        )
        return (
            sum(
                network.flow[commodity, node, head]
                for head in outgoing[node]
            )
            - sum(
                network.flow[commodity, tail, node]
                for tail in incoming[node]
            )
            == net_supply
        )

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=flow_balance_rule
    )

    def shared_capacity_rule(network, tail, head):
        return (
            sum(
                network.flow[commodity, tail, head]
                for commodity in network.commodities
            )
            <= network.arc_capacities[tail, head]
        )

    model.shared_capacity = pyo.Constraint(
        model.arcs, rule=shared_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_costs[tail, head] * model.flow[commodity, tail, head]
            for commodity in model.commodities
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution is available to load.
        # Success is determined exclusively by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}