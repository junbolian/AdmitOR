# IR: {"sets":{"N":"range(num_nodes)","E":"[(0,1),(0,3),(0,5),(1,2),(1,7),(2,3),(2,6),(2,7),(3,4),(4,5),(4,6),(5,6),(6,7),(7,8)]","A":"each edge followed by its reverse, indexed in that order","K":"range(num_commodities)","D":"[0,1]"},"params":{"num_nodes":"params[num_nodes]","node_coordinates":"params[node_coordinates], indexed by node and coordinate","num_edges":"params[num_edges]","num_arcs":"params[num_arcs]","num_commodities":"params[num_commodities]","arc_capacities":"params[arc_capacities], indexed by arc position","arc_unit_costs":"params[arc_unit_costs], indexed by arc position; metadata only","commodity_supply":"params[commodity_supply], indexed by commodity position","commodity_source":"params[commodity_source], indexed by commodity position","commodity_sink":"params[commodity_sink], indexed by commodity position"},"variables":{"flow[k,a]":"continuous nonnegative","max_utilization":"continuous nonnegative"},"constraints":["flow_balance[k,n]: sum(outgoing flow[k,a])-sum(incoming flow[k,a])=supply[k]*(indicator(n=source[k])-indicator(n=sink[k]))","arc_capacity[a]: sum_k flow[k,a]<=capacity[a]","utilization_bound[a]: sum_k flow[k,a]<=capacity[a]*max_utilization"],"objective":"minimize max_utilization"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    node_coordinates = params["node_coordinates"]
    num_edges = params["num_edges"]
    num_arcs = params["num_arcs"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    commodity_supply = params["commodity_supply"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    edges = [
        (0, 1), (0, 3), (0, 5), (1, 2), (1, 7), (2, 3), (2, 6),
        (2, 7), (3, 4), (4, 5), (4, 6), (5, 6), (6, 7), (7, 8),
    ]
    arcs = [
        directed_arc
        for tail, head in edges
        for directed_arc in ((tail, head), (head, tail))
    ]

    if num_edges != len(edges) or num_arcs != len(arcs):
        return {"objective": None, "status": "invalid_network_dimensions"}

    nodes = list(range(num_nodes))
    commodities = list(range(num_commodities))
    arc_indices = list(range(num_arcs))
    node_set = set(nodes)

    if any(tail not in node_set or head not in node_set for tail, head in arcs):
        return {"objective": None, "status": "invalid_node_indices"}

    if any(
        commodity_source[shipment] not in node_set
        or commodity_sink[shipment] not in node_set
        for shipment in commodities
    ):
        return {"objective": None, "status": "invalid_commodity_endpoints"}

    incoming = {
        node: [arc_id for arc_id, (_, head) in enumerate(arcs) if head == node]
        for node in nodes
    }
    outgoing = {
        node: [arc_id for arc_id, (tail, _) in enumerate(arcs) if tail == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(initialize=arc_indices, ordered=True)
    model.K = pyo.Set(initialize=commodities, ordered=True)
    model.D = pyo.Set(initialize=[0, 1], ordered=True)

    model.coordinates = pyo.Param(
        model.N,
        model.D,
        initialize={
            (node, dimension): node_coordinates[node][dimension]
            for node in nodes
            for dimension in (0, 1)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.A,
        initialize={arc_id: arc_capacities[arc_id] for arc_id in arc_indices},
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.A,
        initialize={arc_id: arc_unit_costs[arc_id] for arc_id in arc_indices},
        within=pyo.Reals,
    )
    model.supply = pyo.Param(
        model.K,
        initialize={
            shipment: commodity_supply[shipment] for shipment in commodities
        },
        within=pyo.NonNegativeReals,
    )
    model.source_node = pyo.Param(
        model.K,
        initialize={
            shipment: commodity_source[shipment] for shipment in commodities
        },
        within=model.N,
    )
    model.sink_node = pyo.Param(
        model.K,
        initialize={
            shipment: commodity_sink[shipment] for shipment in commodities
        },
        within=model.N,
    )

    model.flow = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)
    model.max_utilization = pyo.Var(domain=pyo.NonNegativeReals)

    def flow_balance_rule(network, shipment, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[shipment, arc_id] for arc_id in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[shipment, arc_id] for arc_id in incoming[node]
            )
        )
        net_supply = network.supply[shipment] * (
            int(node == pyo.value(network.source_node[shipment]))
            - int(node == pyo.value(network.sink_node[shipment]))
        )
        return net_outflow == net_supply

    model.flow_balance = pyo.Constraint(
        model.K, model.N, rule=flow_balance_rule
    )
    model.arc_capacity = pyo.Constraint(
        model.A,
        rule=lambda network, arc_id: pyo.quicksum(
            network.flow[shipment, arc_id] for shipment in network.K
        ) <= network.capacity[arc_id],
    )
    model.utilization_bound = pyo.Constraint(
        model.A,
        rule=lambda network, arc_id: pyo.quicksum(
            network.flow[shipment, arc_id] for shipment in network.K
        ) <= network.capacity[arc_id] * network.max_utilization,
    )
    model.objective = pyo.Objective(
        expr=model.max_utilization, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this expected error when it cannot load a solution.
        # Objective retrieval below remains the sole success criterion.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}