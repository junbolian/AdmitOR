# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"I":[1,2,3,4,5,6,7,8],"A":[[0,1],[0,6],[0,8],[1,2],[2,3],[2,7],[3,4],[4,5],[4,7],[4,8],[5,6],[6,7],[6,8],[7,8],[8,9]]},"params":{"capacity[u,v]":"params['capacity_u_v'] for (u,v) in A","latency[u,v]":"params['latency_u_v'] for (u,v) in A; descriptive only"},"variables":{"flow[u,v]":{"type":"nonnegative continuous","indices":"A"}},"constraints":["flow[u,v] <= capacity[u,v] for (u,v) in A","sum(flow[u,v] for (u,v) in A if v=k) == sum(flow[u,v] for (u,v) in A if u=k) for k in I"],"objective":{"sense":"maximize","expression":"sum(flow[u,v] for (u,v) in A if u=0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (0, 6),
        (0, 8),
        (1, 2),
        (2, 3),
        (2, 7),
        (3, 4),
        (4, 5),
        (4, 7),
        (4, 8),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
        (8, 9),
    )

    capacities = {
        (0, 1): params["capacity_0_1"],
        (0, 6): params["capacity_0_6"],
        (0, 8): params["capacity_0_8"],
        (1, 2): params["capacity_1_2"],
        (2, 3): params["capacity_2_3"],
        (2, 7): params["capacity_2_7"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (4, 7): params["capacity_4_7"],
        (4, 8): params["capacity_4_8"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (6, 8): params["capacity_6_8"],
        (7, 8): params["capacity_7_8"],
        (8, 9): params["capacity_8_9"],
    }

    latencies = {
        (0, 1): params["latency_0_1"],
        (0, 6): params["latency_0_6"],
        (0, 8): params["latency_0_8"],
        (1, 2): params["latency_1_2"],
        (2, 3): params["latency_2_3"],
        (2, 7): params["latency_2_7"],
        (3, 4): params["latency_3_4"],
        (4, 5): params["latency_4_5"],
        (4, 7): params["latency_4_7"],
        (4, 8): params["latency_4_8"],
        (5, 6): params["latency_5_6"],
        (6, 7): params["latency_6_7"],
        (6, 8): params["latency_6_8"],
        (7, 8): params["latency_7_8"],
        (8, 9): params["latency_8_9"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.intermediate_nodes = pyo.RangeSet(1, 8)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.latency = pyo.Param(
        model.arcs, initialize=latencies, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        inflow = sum(
            network.flow[tail, head]
            for tail, head in network.arcs
            if head == node
        )
        outflow = sum(
            network.flow[tail, head]
            for tail, head in network.arcs
            if tail == node
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_throughput = pyo.Objective(
        expr=sum(
            model.flow[tail, head]
            for tail, head in model.arcs
            if tail == 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}