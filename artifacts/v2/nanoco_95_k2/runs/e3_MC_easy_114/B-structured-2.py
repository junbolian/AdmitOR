# IR: {"sets":{"V":"range(num_nodes)","A":"range(len(arcs))"},"params":{"num_nodes":"params[num_nodes]","source":"params[source]","sink":"params[sink]","coords":"params[coords], frozen metadata","arcs":"params[arcs], ordered directed endpoints","arc_capacities":"params[arc_capacities], physical throughput metadata","arc_unit_costs":"params[arc_unit_costs], signed cut weights"},"variables":{"in_source[v]":"Binary; 1 iff v is in S","crosses[a]":"Binary; 1 iff arc a goes from S to T"},"constraints":["in_source[source] = 1","in_source[sink] = 0","crosses[a] >= in_source[tail[a]] - in_source[head[a]]","crosses[a] <= in_source[tail[a]]","crosses[a] <= 1 - in_source[head[a]]"],"objective":"minimize sum(arc_unit_costs[a] * crosses[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    coords = params["coords"]
    arcs = params["arcs"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    if num_nodes <= 0:
        raise ValueError("num_nodes must be positive.")
    if source not in range(num_nodes) or sink not in range(num_nodes):
        raise ValueError("source and sink must be valid node IDs.")
    if source == sink:
        return {"objective": None, "status": "infeasible"}
    if len(coords) != num_nodes:
        raise ValueError("coords must contain one entry per node.")
    if not (
        len(arcs) == len(arc_capacities) == len(arc_unit_costs)
    ):
        raise ValueError("Arc data lengths must match.")

    for arc_id, endpoints in enumerate(arcs):
        if len(endpoints) != 2:
            raise ValueError("Each arc must have two endpoints.")
        if any(node_id not in range(num_nodes) for node_id in endpoints):
            raise ValueError("Every arc endpoint must be a valid node ID.")
        if arc_capacities[arc_id] < 0:
            raise ValueError("Arc capacities must be nonnegative.")

    # The specified objective weights cuts by unit costs, not capacities.
    # No evacuation demand or flow variable is specified, so capacities
    # remain physical metadata and do not constrain the partition.
    # This cost-minimizing cut need not be a minimum-capacity cut.

    model = pyo.ConcreteModel()
    model.node_ids = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_ids = pyo.Set(initialize=range(len(arcs)), ordered=True)

    model.arc_tail = pyo.Param(
        model.arc_ids,
        initialize={arc_id: arcs[arc_id][0] for arc_id in model.arc_ids},
        within=model.node_ids,
    )
    model.arc_head = pyo.Param(
        model.arc_ids,
        initialize={arc_id: arcs[arc_id][1] for arc_id in model.arc_ids},
        within=model.node_ids,
    )
    model.arc_capacity = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_capacities[arc_id] for arc_id in model.arc_ids
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_unit_costs[arc_id] for arc_id in model.arc_ids
        },
        within=pyo.Reals,
    )

    model.in_source = pyo.Var(model.node_ids, domain=pyo.Binary)
    model.crosses = pyo.Var(model.arc_ids, domain=pyo.Binary)

    model.source_membership = pyo.Constraint(
        expr=model.in_source[source] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.in_source[sink] == 0
    )

    # All three inequalities are necessary to enforce exact crossing
    # indicators when cut weights can be negative.
    def crossing_lower_rule(instance, arc_id):
        tail = pyo.value(instance.arc_tail[arc_id])
        head = pyo.value(instance.arc_head[arc_id])
        return (
            instance.crosses[arc_id]
            >= instance.in_source[tail] - instance.in_source[head]
        )

    def crossing_tail_rule(instance, arc_id):
        tail = pyo.value(instance.arc_tail[arc_id])
        return instance.crosses[arc_id] <= instance.in_source[tail]

    def crossing_head_rule(instance, arc_id):
        head = pyo.value(instance.arc_head[arc_id])
        return instance.crosses[arc_id] <= 1 - instance.in_source[head]

    model.crossing_lower = pyo.Constraint(
        model.arc_ids, rule=crossing_lower_rule
    )
    model.crossing_tail_upper = pyo.Constraint(
        model.arc_ids, rule=crossing_tail_rule
    )
    model.crossing_head_upper = pyo.Constraint(
        model.arc_ids, rule=crossing_head_rule
    )

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.arc_cost[arc_id] * model.crosses[arc_id]
            for arc_id in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this specific error when it cannot load a solution.
        # Unexpected solver exceptions propagate to the calling harness.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}