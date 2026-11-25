# IR: {"sets":{"V":"range(num_nodes)","A":"range(len(arcs))"},"params":{"num_nodes":"params[num_nodes]","source":"params[source]","sink":"params[sink]","coords":"params[coords], frozen and unused","arcs":"params[arcs], directed endpoints indexed by A","arc_capacities":"params[arc_capacities], nonnegative throughput limits","arc_unit_costs":"params[arc_unit_costs], real cut coefficients"},"variables":{"in_source[v]":"binary; 1 iff v is in S","crosses[a]":"binary; 1 iff arc a goes from S to T","flow[a]":"nonnegative real auxiliary evacuation flow","throughput":"nonnegative real auxiliary source-to-sink throughput"},"constraints":["in_source[source] = 1","in_source[sink] = 0","crosses[a] >= in_source[tail[a]] - in_source[head[a]]","crosses[a] <= in_source[tail[a]]","crosses[a] <= 1 - in_source[head[a]]","flow[a] <= arc_capacities[a]","sum(outgoing flow[v]) - sum(incoming flow[v]) = throughput if v=source, -throughput if v=sink, otherwise 0"],"objective":"minimize sum(arc_unit_costs[a] * crosses[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    source = params["source"]
    sink = params["sink"]
    coords = params["coords"]
    arcs = [tuple(arc) for arc in params["arcs"]]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    # Coordinates are frozen metadata and do not enter the cut calculation.
    # No minimum evacuation throughput is specified. Auxiliary flow may be
    # zero, so capacity feasibility does not change the minimum-cost partition.
    # This objective uses unit costs, not capacities or cost-capacity products;
    # it does not assert that the resulting cut is a maximum-flow bottleneck.

    model = pyo.ConcreteModel()

    model.node_ids = pyo.Set(
        initialize=range(num_nodes), ordered=True
    )
    model.arc_ids = pyo.Set(
        initialize=range(len(arcs)), ordered=True
    )

    model.capacity = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_capacities[arc_id]
            for arc_id in range(len(arcs))
        },
        within=pyo.NonNegativeReals,
    )
    model.cut_coefficient = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_unit_costs[arc_id]
            for arc_id in range(len(arcs))
        },
        within=pyo.Reals,
    )

    outgoing = {node: [] for node in range(num_nodes)}
    incoming = {node: [] for node in range(num_nodes)}
    for arc_id, (tail, head) in enumerate(arcs):
        outgoing[tail].append(arc_id)
        incoming[head].append(arc_id)

    model.in_source = pyo.Var(model.node_ids, domain=pyo.Binary)
    model.crosses = pyo.Var(model.arc_ids, domain=pyo.Binary)
    model.flow = pyo.Var(model.arc_ids, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    model.source_membership = pyo.Constraint(
        expr=model.in_source[source] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.in_source[sink] == 0
    )

    def crossing_lower_rule(network, arc_id):
        tail, head = arcs[arc_id]
        return (
            network.crosses[arc_id]
            >= network.in_source[tail] - network.in_source[head]
        )

    def crossing_tail_rule(network, arc_id):
        tail, _ = arcs[arc_id]
        return network.crosses[arc_id] <= network.in_source[tail]

    def crossing_head_rule(network, arc_id):
        _, head = arcs[arc_id]
        return network.crosses[arc_id] <= 1 - network.in_source[head]

    # All three inequalities are required for exact crossing indicators,
    # including when unit costs are negative.
    model.crossing_lower_bound = pyo.Constraint(
        model.arc_ids, rule=crossing_lower_rule
    )
    model.crossing_tail_bound = pyo.Constraint(
        model.arc_ids, rule=crossing_tail_rule
    )
    model.crossing_head_bound = pyo.Constraint(
        model.arc_ids, rule=crossing_head_rule
    )

    def capacity_rule(network, arc_id):
        return network.flow[arc_id] <= network.capacity[arc_id]

    model.throughput_limits = pyo.Constraint(
        model.arc_ids, rule=capacity_rule
    )

    def flow_balance_rule(network, node):
        net_outflow = (
            sum(network.flow[arc_id] for arc_id in outgoing[node])
            - sum(network.flow[arc_id] for arc_id in incoming[node])
        )
        if node == source:
            return net_outflow == network.throughput
        if node == sink:
            return net_outflow == -network.throughput
        # The extra symbolic term also handles isolated nodes.
        return net_outflow + 0 * network.throughput == 0

    model.flow_balance = pyo.Constraint(
        model.node_ids, rule=flow_balance_rule
    )

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.cut_coefficient[arc_id] * model.crosses[arc_id]
            for arc_id in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}