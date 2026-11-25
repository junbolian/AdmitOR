# IR: {"sets":{"N":"range(params['num_nodes'])","K":"range(params['num_commodities'])","A":"arc-list positions, preserving params['arcs'] exactly"},"params":{"num_nodes":"number of nodes","num_commodities":"number of commodities","node_coords_x":"node x-coordinates; data only","node_coords_y":"node y-coordinates; data only","arcs":"directed endpoints in original order","arc_capacity":"positive capacity by arc position","arc_cost":"unit pumping cost by arc position; data only","commodity_demand":"required throughput by commodity","commodity_source":"source node by commodity","commodity_sink":"sink node by commodity"},"variables":{"flow[k,a]":"nonnegative continuous commodity flow","peak_utilization":"continuous in [0,1]"},"constraints":["For each k,n: outgoing flow minus incoming flow = commodity_demand[k] * (1[n=commodity_source[k]] - 1[n=commodity_sink[k]]).","For each a: sum_k flow[k,a] <= arc_capacity[a].","For each a: sum_k flow[k,a] <= peak_utilization * arc_capacity[a]."],"objective":"Minimize peak_utilization."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]
    arcs = tuple(tuple(arc) for arc in params["arcs"])
    arc_capacity = params["arc_capacity"]
    arc_cost = params["arc_cost"]
    commodity_demand = params["commodity_demand"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.K = pyo.Set(initialize=range(num_commodities), ordered=True)
    model.A = pyo.Set(initialize=range(len(arcs)), ordered=True)

    model.node_coords_x = pyo.Param(
        model.N,
        initialize={node: node_coords_x[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )
    model.node_coords_y = pyo.Param(
        model.N,
        initialize={node: node_coords_y[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )
    model.arc_start = pyo.Param(
        model.A,
        initialize={arc_id: arcs[arc_id][0] for arc_id in range(len(arcs))},
        within=model.N,
    )
    model.arc_end = pyo.Param(
        model.A,
        initialize={arc_id: arcs[arc_id][1] for arc_id in range(len(arcs))},
        within=model.N,
    )
    model.arc_capacity = pyo.Param(
        model.A,
        initialize={arc_id: arc_capacity[arc_id] for arc_id in range(len(arcs))},
        within=pyo.PositiveReals,
    )
    model.arc_cost = pyo.Param(
        model.A,
        initialize={arc_id: arc_cost[arc_id] for arc_id in range(len(arcs))},
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
    model.commodity_source = pyo.Param(
        model.K,
        initialize={
            commodity: commodity_source[commodity]
            for commodity in range(num_commodities)
        },
        within=model.N,
    )
    model.commodity_sink = pyo.Param(
        model.K,
        initialize={
            commodity: commodity_sink[commodity]
            for commodity in range(num_commodities)
        },
        within=model.N,
    )

    outgoing = {node: [] for node in range(num_nodes)}
    incoming = {node: [] for node in range(num_nodes)}
    for arc_id, (start_node, end_node) in enumerate(arcs):
        outgoing[start_node].append(arc_id)
        incoming[end_node].append(arc_id)

    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)
    model.peak_utilization = pyo.Var(
        domain=pyo.NonNegativeReals, bounds=(0, 1)
    )

    def balance_rule(network, commodity, node):
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
        source = pyo.value(network.commodity_source[commodity])
        sink = pyo.value(network.commodity_sink[commodity])
        required_balance = network.commodity_demand[commodity] * (
            int(node == source) - int(node == sink)
        )
        return required_balance, net_outflow, required_balance

    model.flow_balance = pyo.Constraint(model.K, model.N, rule=balance_rule)

    model.total_arc_flow = pyo.Expression(
        model.A,
        rule=lambda network, arc_id: pyo.quicksum(
            network.flow[commodity, arc_id] for commodity in network.K
        ),
    )

    model.capacity_limit = pyo.Constraint(
        model.A,
        rule=lambda network, arc_id: (
            network.total_arc_flow[arc_id] <= network.arc_capacity[arc_id]
        ),
    )

    model.utilization_limit = pyo.Constraint(
        model.A,
        rule=lambda network, arc_id: (
            network.total_arc_flow[arc_id]
            <= network.peak_utilization * network.arc_capacity[arc_id]
        ),
    )

    model.objective = pyo.Objective(
        expr=model.peak_utilization, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve may raise before a solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}