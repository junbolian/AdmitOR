# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7],"intermediate":[1,2,3,4,5,6],"arcs":[[0,1],[0,2],[0,3],[0,7],[1,2],[1,5],[2,3],[2,5],[2,6],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{"capacity":"nonnegative real per arc, read from params['capacity'] in arc order","cost":"real per arc, read from params['cost'] in arc order; informational only"},"variables":{"flow":"nonnegative continuous real per arc"},"constraints":["flow[i,j] <= capacity[i,j] for every arc (i,j)","sum(flow[i,v] for incoming arcs) == sum(flow[v,j] for outgoing arcs) for each intermediate node v"],"objective":"maximize sum(flow[0,j] for arcs leaving node 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    capacity_values = params["capacity"]
    cost_values = params["cost"]

    if len(capacity_values) != len(arcs) or len(cost_values) != len(arcs):
        raise ValueError("capacity and cost must each contain 17 entries.")

    capacity_data = {
        arc: capacity_values[position]
        for position, arc in enumerate(arcs)
    }
    cost_data = {
        arc: cost_values[position]
        for position, arc in enumerate(arcs)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(8), ordered=True)
    model.intermediate = pyo.Set(initialize=range(1, 7), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize=cost_data,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, node):
        inflow = sum(
            network.flow[origin, destination]
            for origin, destination in network.arcs
            if destination == node
        )
        outflow = sum(
            network.flow[origin, destination]
            for origin, destination in network.arcs
            if origin == node
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate,
        rule=conservation_rule,
    )

    model.total_throughput = pyo.Objective(
        expr=sum(
            model.flow[origin, destination]
            for origin, destination in model.arcs
            if origin == 0
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