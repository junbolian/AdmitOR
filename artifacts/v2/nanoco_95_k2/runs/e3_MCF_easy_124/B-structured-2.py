# IR: {"sets":{"nodes":[0,1,2,3,4,5],"arcs":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]],"axes":[0,1]},"params":{"supply":"real[nodes], from params['supply']","capacity":"nonnegative real[arcs], from params['capacity'] in arc order","cost":"real[arcs], from params['cost'] in arc order","coords":"real[nodes,axes], from params['coords']; spatial metadata only"},"variables":{"flow":"nonnegative continuous[arcs]"},"constraints":["balance[node]: sum(flow[node,j] for outgoing arcs) - sum(flow[i,node] for incoming arcs) == supply[node]","capacity_limit[i,j]: flow[i,j] <= capacity[i,j]"],"objective":"minimize sum(cost[i,j] * flow[i,j] for all arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = (
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 4),
        (3, 5),
        (0, 4),
        (0, 5),
        (1, 4),
        (1, 5),
    )

    supply = params["supply"]
    capacity = params["capacity"]
    cost = params["cost"]
    coords = params["coords"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.axes = pyo.Set(initialize=(0, 1), ordered=True)

    model.supply = pyo.Param(
        model.nodes,
        initialize={node: supply[node] for node in nodes},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[position] for position, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize={arc: cost[position] for position, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.coords = pyo.Param(
        model.nodes,
        model.axes,
        initialize={
            (node, axis): coords[node][axis]
            for node in nodes
            for axis in (0, 1)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(network, node):
        outflow = sum(
            network.flow[source, target]
            for source, target in arcs
            if source == node
        )
        inflow = sum(
            network.flow[source, target]
            for source, target in arcs
            if target == node
        )
        return outflow - inflow == network.supply[node]

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(network, source, target):
        return (
            network.flow[source, target]
            <= network.capacity[source, target]
        )

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[source, target] * model.flow[source, target]
            for source, target in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}