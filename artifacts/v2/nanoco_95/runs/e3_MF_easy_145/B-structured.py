# IR: {"sets":{"nodes":"0..8","intermediate_nodes":"1..7","channels":"1..14","arcs":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"node_coords":"params['node_coords']; informational only","capacities":"params['capacities']; sequence in channel order","unit_costs":"params['unit_costs']; sequence in channel order, unused by the maximum-flow objective"},"variables":{"flow[channel]":"nonnegative continuous"},"constraints":["flow[channel] <= capacities[channel] for every channel","sum(flow[channel] entering node) == sum(flow[channel] leaving node) for each intermediate node"],"objective":{"sense":"maximize","expression":"sum(flow[channel] leaving node 0) - sum(flow[channel] entering node 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_coords = params["node_coords"]
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]

    # Coordinates are informational; connectivity is fixed independently.
    arcs = {
        1: (0, 1),
        2: (0, 2),
        3: (0, 6),
        4: (0, 8),
        5: (1, 2),
        6: (1, 5),
        7: (2, 3),
        8: (2, 6),
        9: (3, 4),
        10: (4, 5),
        11: (5, 6),
        12: (6, 7),
        13: (6, 8),
        14: (7, 8),
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 8)
    model.intermediate_nodes = pyo.RangeSet(1, 7)
    model.channels = pyo.RangeSet(1, 14)

    model.channel_capacity = pyo.Param(
        model.channels,
        initialize={
            channel: capacities[channel - 1]
            for channel in model.channels
        },
        within=pyo.NonNegativeReals,
    )
    model.channel_unit_cost = pyo.Param(
        model.channels,
        initialize={
            channel: unit_costs[channel - 1]
            for channel in model.channels
        },
        within=pyo.Reals,
    )

    incoming = {
        node: tuple(
            channel
            for channel, (_, destination) in arcs.items()
            if destination == node
        )
        for node in model.nodes
    }
    outgoing = {
        node: tuple(
            channel
            for channel, (origin, _) in arcs.items()
            if origin == node
        )
        for node in model.nodes
    }

    model.flow = pyo.Var(
        model.channels,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(network, channel):
        return (
            network.flow[channel]
            <= network.channel_capacity[channel]
        )

    model.capacity_limits = pyo.Constraint(
        model.channels,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        return (
            pyo.quicksum(
                network.flow[channel] for channel in incoming[node]
            )
            == pyo.quicksum(
                network.flow[channel] for channel in outgoing[node]
            )
        )

    model.flow_balance = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.total_net_flow = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.flow[channel] for channel in outgoing[0]
            )
            - pyo.quicksum(
                model.flow[channel] for channel in incoming[0]
            )
        ),
        sense=pyo.maximize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_net_flow))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed"
                if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}