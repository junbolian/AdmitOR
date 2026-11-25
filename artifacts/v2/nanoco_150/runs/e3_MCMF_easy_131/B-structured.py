# IR: {"sets":{"nodes":"0..9","intermediate_nodes":"1..8","arcs":[[0,1],[1,2],[1,7],[2,3],[2,6],[3,4],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},"params":{"capacities":"nonnegative real per arc, from params","unit_costs":"real per arc, from params","node_coords_x":"fixed real per node, from params; metadata only","node_coords_y":"fixed real per node, from params; metadata only"},"variables":{"flow[a]":"continuous nonnegative real"},"expressions":{"delivered":"sum(flow[a] for arcs leaving node 0) - sum(flow[a] for arcs entering node 0)","total_cost":"sum(unit_costs[a] * flow[a] for all arcs)"},"constraints":["flow[a] <= capacities[a] for every arc","sum(incoming flow) = sum(outgoing flow) at each intermediate node","stage 2 only: delivered = optimal stage 1 delivered"],"objective":{"priority_1":"maximize delivered","priority_2":"fix optimal delivered and minimize total_cost","returned_objective":"optimal total_cost"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (1, 2),
        (1, 7),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 8),
        (5, 6),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    )

    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]

    incoming = {
        node: tuple(
            arc_idx
            for arc_idx, (_, destination) in enumerate(arcs)
            if destination == node
        )
        for node in range(10)
    }
    outgoing = {
        node: tuple(
            arc_idx
            for arc_idx, (origin, _) in enumerate(arcs)
            if origin == node
        )
        for node in range(10)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.intermediate_nodes = pyo.RangeSet(1, 8)
    model.arc_ids = pyo.RangeSet(0, 14)

    model.capacities = pyo.Param(
        model.arc_ids,
        initialize={arc_idx: capacities[arc_idx] for arc_idx in range(15)},
        within=pyo.NonNegativeReals,
    )
    model.unit_costs = pyo.Param(
        model.arc_ids,
        initialize={arc_idx: unit_costs[arc_idx] for arc_idx in range(15)},
        within=pyo.Reals,
    )
    model.node_coords_x = pyo.Param(
        model.nodes,
        initialize={node: node_coords_x[node] for node in range(10)},
        within=pyo.Reals,
    )
    model.node_coords_y = pyo.Param(
        model.nodes,
        initialize={node: node_coords_y[node] for node in range(10)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arc_ids, domain=pyo.NonNegativeReals)

    def capacity_rule(current_model, arc_idx):
        return current_model.flow[arc_idx] <= current_model.capacities[arc_idx]

    model.capacity_limits = pyo.Constraint(
        model.arc_ids, rule=capacity_rule
    )

    def conservation_rule(current_model, node):
        return (
            sum(current_model.flow[arc_idx] for arc_idx in incoming[node])
            == sum(current_model.flow[arc_idx] for arc_idx in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.delivered = pyo.Expression(
        expr=(
            sum(model.flow[arc_idx] for arc_idx in outgoing[0])
            - sum(model.flow[arc_idx] for arc_idx in incoming[0])
        )
    )
    model.total_cost = pyo.Expression(
        expr=sum(
            model.unit_costs[arc_idx] * model.flow[arc_idx]
            for arc_idx in model.arc_ids
        )
    )

    model.volume_objective = pyo.Objective(
        expr=model.delivered, sense=pyo.maximize
    )
    model.cost_objective = pyo.Objective(
        expr=model.total_cost, sense=pyo.minimize
    )
    model.cost_objective.deactivate()

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_1_failed"}

    try:
        obj_val = float(pyo.value(model.volume_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_1_no_objective"}

    model.maximum_delivery = pyo.Constraint(
        expr=model.delivered == obj_val
    )
    model.volume_objective.deactivate()
    model.cost_objective.activate()

    # Clear the first-stage solution so objective retrieval requires
    # values loaded by the second solve.
    for arc_idx in model.arc_ids:
        model.flow[arc_idx].set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_2_failed"}

    try:
        obj_val = float(pyo.value(model.cost_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_2_no_objective"}

    return {"objective": obj_val, "status": "optimal"}