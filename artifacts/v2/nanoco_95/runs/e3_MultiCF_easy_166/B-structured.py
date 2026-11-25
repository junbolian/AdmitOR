# IR: {"sets":{"N":"range(num_nodes)","A":"range(num_arcs), indexed by ordered arcs","K":"range(num_commodities)"},"params":{"num_nodes":"params[num_nodes], frozen at 10","num_arcs":"params[num_arcs], frozen at 30","num_commodities":"params[num_commodities], frozen at 2","arc_capacity":"params[arc_capacity][a]","arc_cost":"params[arc_cost][a]","commodity_demand":"params[commodity_demand][k]","source":[1,0],"sink":[7,4]},"variables":{"flow[k,a]":"nonnegative continuous real"},"constraints":["For each k,n: sum(flow[k,a] for arcs leaving n) - sum(flow[k,a] for arcs entering n) = commodity_demand[k]*(1[n=source[k]]-1[n=sink[k]]).","For each a: sum(flow[k,a] for k in K) <= arc_capacity[a]."],"objective":"Minimize sum(arc_cost[a]*flow[k,a] for k in K for a in A)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]

    if (num_nodes, num_arcs, num_commodities) != (10, 30, 2):
        return {"objective": None, "status": "invalid_dimensions"}

    if (
        len(arc_capacity) != num_arcs
        or len(arc_cost) != num_arcs
        or len(commodity_demand) != num_commodities
    ):
        return {"objective": None, "status": "invalid_data_lengths"}

    arcs = (
        (0, 1), (1, 0), (0, 4), (4, 0),
        (1, 2), (2, 1), (1, 5), (5, 1),
        (2, 3), (3, 2), (2, 6), (6, 2),
        (3, 4), (4, 3), (3, 9), (9, 3),
        (4, 5), (5, 4), (4, 6), (6, 4),
        (5, 6), (6, 5), (5, 7), (7, 5),
        (6, 7), (7, 6), (7, 8), (8, 7),
        (8, 9), (9, 8),
    )
    sources = (1, 0)
    sinks = (7, 4)

    outgoing = {
        node: tuple(
            arc_id for arc_id, (tail, head) in enumerate(arcs)
            if tail == node
        )
        for node in range(num_nodes)
    }
    incoming = {
        node: tuple(
            arc_id for arc_id, (tail, head) in enumerate(arcs)
            if head == node
        )
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.A = pyo.Set(initialize=range(num_arcs), ordered=True)
    model.K = pyo.Set(initialize=range(num_commodities), ordered=True)

    model.arc_capacity = pyo.Param(
        model.A,
        initialize={arc_id: arc_capacity[arc_id] for arc_id in range(num_arcs)},
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.A,
        initialize={arc_id: arc_cost[arc_id] for arc_id in range(num_arcs)},
        within=pyo.Reals,
    )
    model.commodity_demand = pyo.Param(
        model.K,
        initialize={
            commodity: commodity_demand[commodity]
            for commodity in range(num_commodities)
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)

    def flow_balance_rule(network, commodity, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[commodity, arc_id]
                for arc_id in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[commodity, arc_id]
                for arc_id in incoming[node]
            )
        )
        required_net_outflow = network.commodity_demand[commodity] * (
            int(node == sources[commodity])
            - int(node == sinks[commodity])
        )
        return net_outflow == required_net_outflow

    model.flow_balance = pyo.Constraint(
        model.K, model.N, rule=flow_balance_rule
    )

    def shared_capacity_rule(network, arc_id):
        return (
            pyo.quicksum(
                network.flow[commodity, arc_id]
                for commodity in network.K
            )
            <= network.arc_capacity[arc_id]
        )

    model.shared_capacity = pyo.Constraint(
        model.A, rule=shared_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.arc_cost[arc_id] * model.flow[commodity, arc_id]
            for commodity in model.K
            for arc_id in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when no feasible solution can be loaded.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}