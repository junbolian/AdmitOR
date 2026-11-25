# IR: {"sets":{"nodes":[0,1,2,3,4,5],"axes":[0,1],"arcs":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supply":"real[nodes], from params['supply']","capacity":"nonnegative real[arcs], from params['capacity'] in listed arc order","cost":"real[arcs], from params['cost'] in listed arc order","coords":"real[nodes,axes], from params['coords']; spatial metadata only"},"variables":{"flow":"nonnegative continuous[arcs]"},"constraints":["balance[node]: sum(flow[node,j]) - sum(flow[i,node]) == supply[node]","capacity_limit[i,j]: flow[i,j] <= capacity[i,j]"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    axes = (0, 1)
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

    supply_data = params["supply"]
    capacity_data = params["capacity"]
    cost_data = params["cost"]
    coords_data = params["coords"]

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.axes = pyo.Set(initialize=axes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(
        model.nodes,
        initialize={node: supply_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacity_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize={
            arc: cost_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.coords = pyo.Param(
        model.nodes,
        model.axes,
        initialize={
            (node, axis): coords_data[node][axis]
            for node in nodes
            for axis in axes
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(network, node):
        return (
            sum(network.flow[arc] for arc in outgoing[node])
            - sum(network.flow[arc] for arc in incoming[node])
            == network.supply[node]
        )

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}